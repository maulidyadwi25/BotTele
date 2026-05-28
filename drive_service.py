# drive_service.py
import os
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Path ke file kredensial service account Anda
SERVICE_ACCOUNT_FILE = 'credentials.json'

def get_drive_service():
    """Membuat dan mengembalikan service object untuk Google Drive API."""
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    service = build('drive', 'v3', credentials=creds)
    return service

def get_file_modification_time(file_id):
    """
    Get the modifiedTime of a file from Google Drive API.
    Returns the modifiedTime string or None if error.
    """
    try:
        service = get_drive_service()
        file_meta = service.files().get(
            fileId=file_id,
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
    """
    service = get_drive_service()
    
    # Dapatkan semua folder di dalam folder_id
    folder_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    folder_results = service.files().list(q=folder_query, fields="files(id, name)").execute()
    folders = folder_results.get('files', [])
    
    # Dapatkan file spreadsheet di folder root SAJA (tidak dari subfolder)
    spreadsheet_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    spreadsheet_results = service.files().list(q=spreadsheet_query, fields="files(id, name, parents)").execute()
    files = spreadsheet_results.get('files', [])
    
    # Tambahkan informasi folder ke setiap file
    for file in files:
        file['is_folder'] = False
        file['parent_folder_id'] = folder_id
    
    # Tambahkan folder sebagai entitas terpisah untuk navigasi
    for folder in folders:
        files.append({
            'id': folder['id'],
            'name': folder['name'],
            'is_folder': True,
            'parent_folder_id': folder_id
        })
    
    return files

def get_all_spreadsheets_recursive(folder_id, depth=0, max_depth=10, current_path=""):
    """
    Recursively get all spreadsheet files from folder and its subfolders.
    
    Args:
        folder_id: The ID of the folder to start from
        depth: Current recursion depth (internal use)
        max_depth: Maximum recursion depth to prevent infinite loops (default: 10)
        current_path: Current folder path for display purposes
    
    Returns:
        List of dicts with 'id', 'name', 'is_folder', 'parent_folder_id', and 'folder_path'
    """
    if depth > max_depth:
        return []
    
    service = get_drive_service()
    all_files = []
    
    # Get folders in current level
    folder_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    folder_results = service.files().list(q=folder_query, fields="files(id, name)").execute()
    folders = folder_results.get('files', [])
    
    # Get spreadsheets in current level
    spreadsheet_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    spreadsheet_results = service.files().list(q=spreadsheet_query, fields="files(id, name, parents)").execute()
    spreadsheets = spreadsheet_results.get('files', [])
    
    # Process spreadsheets
    for file in spreadsheets:
        file['is_folder'] = False
        file['parent_folder_id'] = folder_id
        file['folder_path'] = current_path
        all_files.append(file)
    
    # Process subfolders recursively
    for folder in folders:
        folder_info = {
            'id': folder['id'],
            'name': folder['name'],
            'is_folder': True,
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