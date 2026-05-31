# drive_service.py
import os
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Path ke file kredensial service account Anda
SERVICE_ACCOUNT_FILE = 'credentials.json'

# MimeType constant for spreadsheet shortcuts
SHORTCUT_MIMETYPE = 'application/vnd.google-apps.shortcut'
SPREADSHEET_MIMETYPE = 'application/vnd.google-apps.spreadsheet'
FOLDER_MIMETYPE = 'application/vnd.google-apps.folder'


def get_drive_service():
    """Membuat dan mengembalikan service object untuk Google Drive API."""
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    service = build('drive', 'v3', credentials=creds)
    return service


def resolve_shortcut(file_id):
    """
    Resolve a shortcut to its target file ID.
    
    Args:
        file_id: The file ID of the shortcut
        
    Returns:
        Tuple of (target_file_id, target_mime_type) or (None, None) if not a shortcut or error
    """
    try:
        service = get_drive_service()
        file_meta = service.files().get(
            fileId=file_id,
            fields='mimeType,shortcutDetails'
        ).execute()
        
        mime_type = file_meta.get('mimeType')
        
        # Check if this is a shortcut
        if mime_type == SHORTCUT_MIMETYPE:
            shortcut_details = file_meta.get('shortcutDetails', {})
            target_id = shortcut_details.get('targetId')
            target_mime = shortcut_details.get('targetMimeType')
            return target_id, target_mime
        
        # Not a shortcut, return the file_id itself
        return file_id, mime_type
        
    except Exception as e:
        print(f"[ERROR] resolve_shortcut: {e}")
        return None, None


def resolve_file_id(file_id):
    """
    Resolve any file ID (shortcut or direct) to the actual spreadsheet file ID.
    Returns the target spreadsheet ID if it's a shortcut to a spreadsheet,
    or the original ID if it's already a spreadsheet.
    
    Args:
        file_id: The file ID to resolve
        
    Returns:
        Target spreadsheet file ID, or original file_id if not a shortcut
    """
    target_id, target_mime = resolve_shortcut(file_id)
    
    if target_id is None:
        # Error occurred, return original
        return file_id
    
    # If target is a spreadsheet, return the target ID
    if target_mime == SPREADSHEET_MIMETYPE:
        return target_id
    
    # If target is a shortcut to something else (not a spreadsheet), 
    # we still return the target_id as that's what the shortcut points to
    # The calling code should handle non-spreadsheet targets appropriately
    return target_id


def get_file_modification_time(file_id):
    """
    Get the modifiedTime of a file from Google Drive API.
    If file_id is a shortcut, resolves to the target file first.
    Returns the modifiedTime string or None if error.
    """
    try:
        # Resolve shortcut if needed
        resolved_id = resolve_file_id(file_id)
        
        service = get_drive_service()
        file_meta = service.files().get(
            fileId=resolved_id,
            fields='modifiedTime'
        ).execute()
        return file_meta.get('modifiedTime')
    except Exception as e:
        print(f"[ERROR] get_file_modification_time: {e}")
        return None


def list_spreadsheet_files(folder_id):
    """
    Mengambil daftar folder dan file spreadsheet di folder root.
    Hanya menampilkan folder di root, tidak menampilkan file dari subfolder.
    Mendukung pintasan (shortcuts) ke spreadsheet.
    """
    service = get_drive_service()
    
    # Dapatkan semua folders di dalam folder_id
    folder_query = f"'{folder_id}' in parents and mimeType='{FOLDER_MIMETYPE}' and trashed=false"
    folder_results = service.files().list(q=folder_query, fields="files(id, name)").execute()
    folders = folder_results.get('files', [])
    
    files = []
    
    # Dapatkan file spreadsheet DAN pintasan spreadsheet di folder root
    # Query untuk spreadsheet langsung
    spreadsheet_query = f"'{folder_id}' in parents and mimeType='{SPREADSHEET_MIMETYPE}' and trashed=false"
    spreadsheet_results = service.files().list(q=spreadsheet_query, fields="files(id, name, parents)").execute()
    spreadsheets = spreadsheet_results.get('files', [])
    
    # Query untuk pintasan (shortcuts)
    shortcut_query = f"'{folder_id}' in parents and mimeType='{SHORTCUT_MIMETYPE}' and trashed=false"
    shortcut_results = service.files().list(q=shortcut_query, fields="files(id, name, shortcutDetails)").execute()
    shortcuts = shortcut_results.get('files', [])
    
    # Process spreadsheets
    for file in spreadsheets:
        file['is_folder'] = False
        file['parent_folder_id'] = folder_id
        file['is_shortcut'] = False
        files.append(file)
    
    # Process shortcuts - resolve and add if they point to spreadsheets
    for shortcut in shortcuts:
        target_id, target_mime = resolve_shortcut(shortcut['id'])
        
        if target_id and target_mime == SPREADSHEET_MIMETYPE:
            # This shortcut points to a spreadsheet
            shortcut['is_folder'] = False
            shortcut['is_shortcut'] = True
            shortcut['parent_folder_id'] = folder_id
            shortcut['target_id'] = target_id  # Store the resolved target ID
            files.append(shortcut)
        else:
            print(f"[DEBUG] Skipping shortcut '{shortcut.get('name')}' - target is not a spreadsheet")
    
    # Tambahkan folders sebagai entitas terpisah untuk navigasi
    for folder in folders:
        files.append({
            'id': folder['id'],
            'name': folder['name'],
            'is_folder': True,
            'parent_folder_id': folder_id,
            'is_shortcut': False
        })
    
    return files


def get_all_spreadsheets_recursive(folder_id, depth=0, max_depth=10, current_path=""):
    """
    Recursively get all spreadsheet files from folder and its subfolders.
    Mendukung pintasan (shortcuts) ke spreadsheet.
    
    Args:
        folder_id: The ID of the folder to start from
        depth: Current recursion depth (internal use)
        max_depth: Maximum recursion depth to prevent infinite loops (default: 10)
        current_path: Current folder path for display purposes
    
    Returns:
        List of dicts with 'id', 'name', 'is_folder', 'parent_folder_id', 'folder_path', 'is_shortcut'
    """
    if depth > max_depth:
        return []
    
    service = get_drive_service()
    all_files = []
    
    # Get folders in current level
    folder_query = f"'{folder_id}' in parents and mimeType='{FOLDER_MIMETYPE}' and trashed=false"
    folder_results = service.files().list(q=folder_query, fields="files(id, name)").execute()
    folders = folder_results.get('files', [])
    
    # Get spreadsheets in current level
    spreadsheet_query = f"'{folder_id}' in parents and mimeType='{SPREADSHEET_MIMETYPE}' and trashed=false"
    spreadsheet_results = service.files().list(q=spreadsheet_query, fields="files(id, name, parents)").execute()
    spreadsheets = spreadsheet_results.get('files', [])
    
    # Get shortcuts in current level
    shortcut_query = f"'{folder_id}' in parents and mimeType='{SHORTCUT_MIMETYPE}' and trashed=false"
    shortcut_results = service.files().list(q=shortcut_query, fields="files(id, name, shortcutDetails)").execute()
    shortcuts = shortcut_results.get('files', [])
    
    # Process spreadsheets
    for file in spreadsheets:
        file['is_folder'] = False
        file['is_shortcut'] = False
        file['parent_folder_id'] = folder_id
        file['folder_path'] = current_path
        all_files.append(file)
    
    # Process shortcuts
    for shortcut in shortcuts:
        target_id, target_mime = resolve_shortcut(shortcut['id'])
        
        if target_id and target_mime == SPREADSHEET_MIMETYPE:
            shortcut['is_folder'] = False
            shortcut['is_shortcut'] = True
            shortcut['parent_folder_id'] = folder_id
            shortcut['folder_path'] = current_path
            shortcut['target_id'] = target_id
            all_files.append(shortcut)
        else:
            print(f"[DEBUG] Skipping shortcut '{shortcut.get('name')}' - target is not a spreadsheet")
    
    # Process subfolders recursively
    for folder in folders:
        folder_info = {
            'id': folder['id'],
            'name': folder['name'],
            'is_folder': True,
            'is_shortcut': False,
            'parent_folder_id': folder_id,
            'folder_path': current_path
        }
        all_files.append(folder_info)
        
        # Recursively get files from subfolder
        new_path = f"{current_path}/{folder['name']}" if current_path else folder['name']
        subfolder_files = get_all_spreadsheets_recursive(
            folder['id'],
            depth=depth + 1,
            max_depth=max_depth,
            current_path=new_path
        )
        all_files.extend(subfolder_files)
    
    return all_files
