# gsheets_service.py (versi yang diperbarui)
import os
import gspread
from google.oauth2.service_account import Credentials
from drive_service import list_spreadsheet_files, get_drive_service

# Konfigurasi
FOLDER_ID = os.getenv('FOLDER_ID', 'YOUR_FOLDER_ID')  # Ganti dengan ID folder Google Drive Anda
SERVICE_ACCOUNT_FILE = 'credentials.json'

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

def get_file_name(file_id):
    """
    Mengambil nama file berdasarkan ID.
    """
    from drive_service import get_drive_service
    service = get_drive_service()
    try:
        file_meta = service.files().get(fileId=file_id, fields="name").execute()
        return file_meta.get('name', 'Unknown')
    except Exception as e:
        print(f"Error getting file name: {e}")
        return 'Unknown'

def get_sheets_from_file(file_id):
    """
    Mengambil daftar sheet (worksheet) dari file spreadsheet tertentu.
    Mengembalikan list of sheet names.
    """
    client = get_sheets_client()
    try:
        spreadsheet = client.open_by_key(file_id)
        worksheets = spreadsheet.worksheets()
        return [worksheet.title for worksheet in worksheets]
    except Exception as e:
        print(f"Error getting sheets from file {file_id}: {e}")
        return []

def get_sheet_data(file_id, sheet_name):
    """
    Mengambil data dari sheet tertentu.
    """
    client = get_sheets_client()
    try:
        spreadsheet = client.open_by_key(file_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_values()
        return data
    except Exception as e:
        print(f"Error getting sheet data: {e}")
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