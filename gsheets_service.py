# gsheets_service.py (versi yang diperbarui)
import os
import time
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
from drive_service import list_spreadsheet_files, get_drive_service, get_all_spreadsheets_recursive

# Konfigurasi
FOLDER_ID = os.getenv('FOLDER_ID', 'YOUR_FOLDER_ID')  # Ganti dengan ID folder Google Drive Anda
SERVICE_ACCOUNT_FILE = 'credentials.json'

# Cache untuk sheet metadata (file_id -> {sheets: [...], timestamp: ...})
SHEET_METADATA_CACHE = {}
SHEET_METADATA_TTL = 600  # 10 minutes - longer cache

# Cache untuk sheet data ((file_id, sheet_name) -> {data: [...], timestamp: ...})
SHEET_DATA_CACHE = {}
SHEET_DATA_TTL = 300  # 5 minutes - longer cache

# File index cache - stores file metadata indexed by file_id
# Automatically updated when accessing files, no separate API calls needed
FILE_INDEX_CACHE = {}  # file_id -> {name, folder_path, last_accessed}
FILE_INDEX_TTL = 3600  # 1 hour - refreshed on each access

# Rate limiting - increased to prevent 429 errors
LAST_REQUEST_TIME = {}
MIN_REQUEST_INTERVAL = 1.0  # 1 second between requests per file

# Exponential backoff for 429 errors
MAX_RETRIES = 3
INITIAL_BACKOFF = 2  # 2 seconds

# Request counter for tracking API calls per message
REQUEST_COUNTER = {
    'count': 0,
    'message_id': None
}

def _increment_request(file_id, operation):
    """
    Track API request count per message for debugging.
    """
    import threading
    thread_id = threading.get_ident()
    if REQUEST_COUNTER['message_id'] != thread_id:
        REQUEST_COUNTER['count'] = 0
        REQUEST_COUNTER['message_id'] = thread_id
    
    REQUEST_COUNTER['count'] += 1
    print(f"[API REQUEST #{REQUEST_COUNTER['count']}] {operation} - file: {file_id[:20]}...")
    return REQUEST_COUNTER['count']

def get_request_count():
    """Get current request count for this message"""
    return REQUEST_COUNTER['count']

def get_sheets_client():
    """Membuat dan mengembalikan client untuk Google Sheets API."""
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    return gspread.authorize(creds)

def get_spreadsheet_files():
    """
    Mengambil daftar file spreadsheet dari folder Google Drive.
    Mengembalikan list of dicts dengan 'id' dan 'name'.
    """
    return list_spreadsheet_files(FOLDER_ID)

def get_all_spreadsheet_files_recursive():
    """
    Mengambil daftar file spreadsheet dari folder Google Drive termasuk subfolder.
    Mengembalikan list of dicts dengan 'id', 'name', dan 'folder_path'.
    """
    return get_all_spreadsheets_recursive(FOLDER_ID)

def get_file_name(file_id):
    """
    Mengambil nama file berdasarkan ID.
    Updates the file index cache when accessing the file.
    """
    # Check if we have it cached
    if file_id in FILE_INDEX_CACHE:
        return FILE_INDEX_CACHE[file_id].get('name', 'Unknown')
    
    from drive_service import get_drive_service
    service = get_drive_service()
    try:
        file_meta = service.files().get(fileId=file_id, fields="name").execute()
        name = file_meta.get('name', 'Unknown')
        
        # Update file index
        FILE_INDEX_CACHE[file_id] = {
            'name': name,
            'folder_path': '',
            'last_accessed': time.time()
        }
        
        return name
    except Exception as e:
        print(f"Error getting file name: {e}")
        return 'Unknown'

def _update_file_index(file_id, file_name, folder_path=""):
    """
    Update the file index when a file is accessed.
    This captures file name changes without needing separate API calls.
    """
    FILE_INDEX_CACHE[file_id] = {
        'name': file_name,
        'folder_path': folder_path,
        'last_accessed': time.time()
    }

def get_file_index():
    """
    Get the current file index.
    Returns dict of file_id -> {name, folder_path, last_accessed}
    """
    return FILE_INDEX_CACHE.copy()

def _rate_limit(file_id):
    """
    Ensure minimum interval between API calls per file.
    """
    current_time = time.time()
    last_time = LAST_REQUEST_TIME.get(file_id, 0)
    elapsed = current_time - last_time
    
    if elapsed < MIN_REQUEST_INTERVAL:
        sleep_time = MIN_REQUEST_INTERVAL - elapsed
        print(f"[RATE LIMIT] Sleeping {sleep_time:.2f}s before request for {file_id[:20]}...")
        time.sleep(sleep_time)
    
    LAST_REQUEST_TIME[file_id] = time.time()

def _handle_rate_limit_error(file_id, retry_count):
    """
    Handle 429 rate limit error with exponential backoff.
    """
    backoff_time = INITIAL_BACKOFF * (2 ** retry_count)
    print(f"[RATE LIMIT] 429 error for {file_id[:20]}... Waiting {backoff_time}s before retry (attempt {retry_count + 1}/{MAX_RETRIES})")
    time.sleep(backoff_time)
    LAST_REQUEST_TIME[file_id] = time.time()  # Reset after backoff

def get_sheets_from_file(file_id):
    """
    Mengambil daftar sheet (worksheet) dari file spreadsheet tertentu.
    Menggunakan cache untuk mengurangi API calls.
    """
    # Check cache first
    current_time = time.time()
    if file_id in SHEET_METADATA_CACHE:
        cached = SHEET_METADATA_CACHE[file_id]
        if current_time - cached['timestamp'] < SHEET_METADATA_TTL:
            print(f"[CACHE HIT] get_sheets_from_file - {file_id[:20]}...")
            return cached['sheets']
        else:
            print(f"[CACHE EXPIRED] get_sheets_from_file - {file_id[:20]}... (age: {current_time - cached['timestamp']:.0f}s)")
    
    # Apply rate limiting
    _rate_limit(file_id)
    _increment_request(file_id, "get_sheets_from_file")
    
    client = get_sheets_client()
    
    for retry in range(MAX_RETRIES):
        try:
            spreadsheet = client.open_by_key(file_id)
            
            # Update file index with current name (captures name changes)
            spreadsheet_name = spreadsheet.title if hasattr(spreadsheet, 'title') else None
            if spreadsheet_name:
                _update_file_index(file_id, spreadsheet_name)
            
            worksheets = spreadsheet.worksheets()
            sheets = [worksheet.title for worksheet in worksheets]
            
            # Store in cache
            SHEET_METADATA_CACHE[file_id] = {
                'sheets': sheets,
                'timestamp': time.time()
            }
            print(f"[CACHE MISS] get_sheets_from_file cached {len(sheets)} sheets - {file_id[:20]}...")
            
            return sheets
        except HttpError as e:
            if e.resp.status == 429:
                _handle_rate_limit_error(file_id, retry)
            else:
                print(f"Error getting sheets from file {file_id}: {e}")
                return []
        except Exception as e:
            error_str = str(e)
            if '429' in error_str:
                _handle_rate_limit_error(file_id, retry)
            else:
                print(f"Error getting sheets from file {file_id}: {e}")
                return []
    
    print(f"Error: Max retries exceeded for getting sheets from file {file_id}")
    return []

def get_sheet_data(file_id, sheet_name):
    """
    Mengambil data dari sheet tertentu.
    Menggunakan cache untuk mengurangi API calls.
    Updates file index when accessing the file.
    """
    cache_key = (file_id, sheet_name)
    
    # Check cache first
    current_time = time.time()
    if cache_key in SHEET_DATA_CACHE:
        cached = SHEET_DATA_CACHE[cache_key]
        if current_time - cached['timestamp'] < SHEET_DATA_TTL:
            print(f"[CACHE HIT] get_sheet_data - {file_id[:20]}... / {sheet_name}")
            # Still update file index on cache hit
            _update_file_index(file_id, FILE_INDEX_CACHE.get(file_id, {}).get('name', 'Unknown'))
            return cached['data']
        else:
            print(f"[CACHE EXPIRED] get_sheet_data - {file_id[:20]}... / {sheet_name} (age: {current_time - cached['timestamp']:.0f}s)")
    
    # Apply rate limiting
    _rate_limit(file_id)
    _increment_request(file_id, "get_sheet_data")
    
    client = get_sheets_client()
    
    for retry in range(MAX_RETRIES):
        try:
            spreadsheet = client.open_by_key(file_id)
            
            # Update file index with current name (captures name changes)
            spreadsheet_name = spreadsheet.title if hasattr(spreadsheet, 'title') else None
            if spreadsheet_name:
                _update_file_index(file_id, spreadsheet_name)
            
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_values()
            
            # Store in cache
            SHEET_DATA_CACHE[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
            
            return data
        except HttpError as e:
            if e.resp.status == 429:
                _handle_rate_limit_error(file_id, retry)
            else:
                print(f"Error getting sheet data: {e}")
                return None
        except Exception as e:
            error_str = str(e)
            if '429' in error_str:
                _handle_rate_limit_error(file_id, retry)
            else:
                print(f"Error getting sheet data: {e}")
                return None
    
    print(f"Error: Max retries exceeded for getting sheet data {file_id}/{sheet_name}")
    return None

def get_files_in_folder(folder_id):
    """
    Mengambil daftar file dan folder dalam folder tertentu.
    """
    service = get_drive_service()
    
    # Dapatkan folder di dalam folder_id
    folder_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    folder_results = service.files().list(q=folder_query, fields="files(id, name)").execute()
    folders = folder_results.get('files', [])
    
    # Dapatkan file spreadsheet di folder_id
    spreadsheet_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    spreadsheet_results = service.files().list(q=spreadsheet_query, fields="files(id, name)").execute()
    spreadsheet_files = spreadsheet_results.get('files', [])
    
    # Buat list untuk semua item (file dan folder)
    files = []
    
    # Tambahkan file spreadsheet
    for file in spreadsheet_files:
        files.append({
            'id': file['id'],
            'name': file['name'],
            'is_folder': False,
            'parent_folder_id': folder_id
        })
    
    # Tambahkan folder sebagai entitas terpisah untuk navigasi
    for folder in folders:
        files.append({
            'id': folder['id'],
            'name': folder['name'],
            'is_folder': True,
            'parent_folder_id': folder_id
        })
    
    return files

def get_all_data_from_folder():
    """
    Mengambil data dari semua spreadsheet dan semua sheet dalam sebuah folder.
    Mengembalikan data dalam format teks yang sudah terstruktur.
    """
    client = get_sheets_client()
    spreadsheet_files = list_spreadsheet_files(FOLDER_ID)

    if not spreadsheet_files:
        return "Tidak ada file spreadsheet yang ditemukan di folder tersebut."

    all_data = ""
    for file in spreadsheet_files:
        file_id = file['id']
        file_name = file['name']

        try:
            spreadsheet = client.open_by_key(file_id)
            all_data += f"\n\n📁 *File:* {file_name}\n"
            all_data += f"   🔗 (ID: {file_id})\n"

            # Iterasi melalui semua sheet yang ada di file spreadsheet
            worksheets = spreadsheet.worksheets()
            for worksheet in worksheets:
                sheet_name = worksheet.title
                all_data += f"\n   📄 *Sheet:* {sheet_name}\n"

                # Ambil data dari sheet, batasi untuk menghindari output terlalu panjang
                data = worksheet.get_all_values()
                if not data:
                    all_data += "      (Sheet kosong)\n"
                    continue

                # Tampilkan beberapa baris pertama sebagai pratinjau
                rows_to_show = min(5, len(data))
                for i in range(rows_to_show):
                    row_data = ' | '.join([str(cell) for cell in data[i]])
                    all_data += f"      Baris {i+1}: {row_data}\n"
                if len(data) > rows_to_show:
                    all_data += f"      ... dan {len(data) - rows_to_show} baris lainnya.\n"

        except Exception as e:
            all_data += f"   ❌ Gagal membaca file {file_name}: {str(e)}\n"

    return all_data