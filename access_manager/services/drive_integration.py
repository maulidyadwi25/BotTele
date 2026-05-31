"""Drive integration service - reuses existing drive_service.py."""
import sys
import os

# Import from parent directory (project root)
# access_manager/services/drive_integration.py -> access_manager/ -> bot-tele/
# Need to go up 3 directories to reach bot-tele root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

try:
    from drive_service import list_spreadsheet_files, get_drive_service, resolve_shortcut, resolve_file_id
    DRIVE_SERVICE_AVAILABLE = True
except ImportError:
    DRIVE_SERVICE_AVAILABLE = False
    print(f"Warning: Could not import drive_service. Project root: {project_root}")

# MimeType constants for shortcut handling
SHORTCUT_MIMETYPE = 'application/vnd.google-apps.shortcut'
SPREADSHEET_MIMETYPE = 'application/vnd.google-apps.spreadsheet'


class DriveIntegration:
    """Integration with Google Drive via existing drive_service.py."""

    def __init__(self):
        self.service = None
        if DRIVE_SERVICE_AVAILABLE:
            try:
                self.service = get_drive_service()
            except Exception as e:
                print(f"Warning: Could not initialize Drive service: {e}")

    def list_files(self, folder_id=None):
        """List files and folders from Google Drive.
        
        Args:
            folder_id: The ID of the folder to list. If None, uses FOLDER_ID from env.
            
        Returns:
            List of files and folders with their metadata.
        """
        if not folder_id:
            folder_id = os.getenv('FOLDER_ID', '')

        if not folder_id:
            return []

        if not DRIVE_SERVICE_AVAILABLE or not self.service:
            return self._get_mock_files()

        try:
            files = list_spreadsheet_files(folder_id)
            return files
        except Exception as e:
            print(f"Error listing files: {e}")
            return self._get_mock_files()

    def _get_mock_files(self):
        """Return mock files when Drive is not available."""
        return [
            {
                'id': 'mock_1',
                'name': 'Sample_Spreadsheet_1.xlsx',
                'is_folder': False,
                'mimeType': 'application/vnd.google-apps.spreadsheet'
            },
            {
                'id': 'mock_2',
                'name': 'Sample_Spreadsheet_2.xlsx',
                'is_folder': False,
                'mimeType': 'application/vnd.google-apps.spreadsheet'
            }
        ]

    def get_file_name(self, file_id):
        """Get the name of a file by ID."""
        if not DRIVE_SERVICE_AVAILABLE or not self.service:
            return 'Unknown File'

        try:
            file = self.service.files().get(fileId=file_id, fields='name').execute()
            return file.get('name', 'Unknown File')
        except Exception as e:
            print(f"Error getting file name: {e}")
            return 'Unknown File'

    def get_files_in_folder(self, folder_id):
        """Get all files in a specific folder, including spreadsheet shortcuts."""
        if not DRIVE_SERVICE_AVAILABLE or not self.service:
            return []

        try:
            all_files = []
            
            # Get regular spreadsheets
            spreadsheet_query = f"'{folder_id}' in parents and mimeType='{SPREADSHEET_MIMETYPE}' and trashed=false"
            spreadsheet_results = self.service.files().list(
                q=spreadsheet_query,
                fields="files(id, name, mimeType)"
            ).execute()
            all_files.extend(spreadsheet_results.get('files', []))
            
            # Get spreadsheet shortcuts
            shortcut_query = f"'{folder_id}' in parents and mimeType='{SHORTCUT_MIMETYPE}' and trashed=false"
            shortcut_results = self.service.files().list(
                q=shortcut_query,
                fields="files(id, name, mimeType, shortcutDetails)"
            ).execute()
            
            for shortcut in shortcut_results.get('files', []):
                target_id, target_mime = resolve_shortcut(shortcut['id'])
                if target_id and target_mime == SPREADSHEET_MIMETYPE:
                    # Add shortcut with resolved target info
                    shortcut['is_shortcut'] = True
                    shortcut['target_id'] = target_id
                    all_files.append(shortcut)
            
            return all_files
        except Exception as e:
            print(f"Error getting files in folder: {e}")
            return []
