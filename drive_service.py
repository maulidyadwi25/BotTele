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