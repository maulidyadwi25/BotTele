"""
SpreadsheetIndexService - Manages spreadsheet file/sheet indexing to reduce API calls.

Instead of hitting Google API every time, we:
1. Store file metadata in SQLite database
2. Only re-index when Drive's modifiedTime changes
3. Lazy load - only index when files are actually accessed
"""
import time
import json
from datetime import datetime
from typing import List, Optional, Dict, Tuple

from access_manager.models.bot_db import get_session, SpreadsheetIndex
import sys
sys.path.insert(0, '.')
import gsheets_service as gs
import drive_service as ds


class SpreadsheetIndexService:
    """Service for managing spreadsheet index in database"""
    
    def __init__(self):
        self._session = None
        self._ctx = None
    
    @property
    def session(self):
        if self._session is None:
            self._ctx, self._session = get_session()
        return self._session
    
    def close(self):
        """Close the database session"""
        if self._session:
            self._session.close()
            self._session = None
        if self._ctx:
            self._ctx.pop()
            self._ctx = None
    
    def get_file_index(self, file_id: str) -> Optional[SpreadsheetIndex]:
        """Get file index from database, return None if not found"""
        return self.session.query(SpreadsheetIndex).filter_by(
            file_id=file_id, 
            is_active=True
        ).first()
    
    def get_file_by_name(self, file_name: str) -> Optional[SpreadsheetIndex]:
        """Get file index by exact name match"""
        return self.session.query(SpreadsheetIndex).filter_by(
            file_name=file_name,
            is_active=True
        ).first()
    
    def search_files_by_name(self, query: str) -> List[SpreadsheetIndex]:
        """Search files by name (case-insensitive partial match)"""
        return self.session.query(SpreadsheetIndex).filter(
            SpreadsheetIndex.file_name.ilike(f'%{query}%'),
            SpreadsheetIndex.is_active == True
        ).all()
    
    def search_files_by_sheet(self, sheet_query: str) -> List[SpreadsheetIndex]:
        """Search files that have a sheet matching the query"""
        return self.session.query(SpreadsheetIndex).filter(
            SpreadsheetIndex.sheet_names.ilike(f'%{sheet_query}%'),
            SpreadsheetIndex.is_active == True
        ).all()
    
    def search_files(self, query: str) -> List[SpreadsheetIndex]:
        """Search files by file name OR sheet name"""
        query_lower = query.lower()
        results = []
        seen_ids = set()
        
        # Search by file name
        for idx in self.search_files_by_name(query):
            if idx.file_id not in seen_ids:
                results.append(idx)
                seen_ids.add(idx.file_id)
        
        # Search by sheet name
        for idx in self.search_files_by_sheet(query):
            if idx.file_id not in seen_ids:
                results.append(idx)
                seen_ids.add(idx.file_id)
        
        return results
    
    def get_all_indexed_files(self) -> List[SpreadsheetIndex]:
        """Get all active indexed files"""
        return self.session.query(SpreadsheetIndex).filter_by(
            is_active=True
        ).all()
    
    def needs_reindex(self, file_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a file needs re-indexing based on Drive's modifiedTime.
        Returns (needs_reindex, current_modified_time)
        """
        try:
            # Get current modifiedTime from Drive API
            modified_time = ds.get_file_modification_time(file_id)
            if not modified_time:
                return True, None
            
            # Get stored modifiedTime from DB
            db_entry = self.get_file_index(file_id)
            if not db_entry:
                return True, modified_time
            
            # Compare
            if db_entry.last_modified != modified_time:
                return True, modified_time
            
            return False, modified_time
        except Exception as e:
            print(f"[ERROR] SpreadsheetIndexService.needs_reindex: {e}")
            return True, None
    
    def index_file(self, file_id: str, file_name: str = None, 
                   folder_id: str = None, folder_path: str = None) -> SpreadsheetIndex:
        """
        Index a single file - fetch sheet names from API and store in DB.
        Only re-fetches if Drive's modifiedTime has changed.
        """
        needs_reindex, current_modified = self.needs_reindex(file_id)
        
        if not needs_reindex:
            print(f"[DEBUG] SpreadsheetIndex: '{file_name or file_id}' - using cached index")
            return self.get_file_index(file_id)
        
        print(f"[DEBUG] SpreadsheetIndex: '{file_name or file_id}' - re-indexing...")
        
        # Get fresh data from API
        try:
            # Get sheet names
            sheets = gs.get_sheets_from_file(file_id)
            
            # Get file metadata if not provided
            if not file_name:
                file_meta = ds.get_drive_service().files().get(
                    fileId=file_id, 
                    fields='name,modifiedTime,parents'
                ).execute()
                file_name = file_meta.get('name', 'Unknown')
                current_modified = file_meta.get('modifiedTime')
                
                # Get folder path
                parent_ids = file_meta.get('parents', [])
                if parent_ids:
                    folder_id = parent_ids[0]
            
            # Upsert index entry
            index_entry = self.get_file_index(file_id)
            if not index_entry:
                index_entry = SpreadsheetIndex(file_id=file_id)
                self.session.add(index_entry)
            
            index_entry.file_name = file_name
            index_entry.folder_id = folder_id
            index_entry.folder_path = folder_path
            index_entry.set_sheet_list(sheets)
            index_entry.last_modified = current_modified
            index_entry.last_indexed = datetime.utcnow()
            index_entry.is_active = True
            
            self.session.commit()
            
            print(f"[DEBUG] SpreadsheetIndex: '{file_name}' indexed with {len(sheets)} sheets")
            return index_entry
            
        except Exception as e:
            self.session.rollback()
            print(f"[ERROR] SpreadsheetIndexService.index_file: {e}")
            raise
    
    def index_all_files(self, file_list: List[Dict] = None) -> int:
        """
        Index all files from Drive or provided list.
        Returns number of files indexed.
        """
        if file_list is None:
            file_list = gs.get_all_spreadsheet_files_recursive()
        
        indexed_count = 0
        for file_info in file_list:
            if file_info.get('is_folder', False):
                continue
            
            try:
                self.index_file(
                    file_id=file_info['id'],
                    file_name=file_info.get('name'),
                    folder_id=file_info.get('parent_id'),
                    folder_path=file_info.get('folder_path', '')
                )
                indexed_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to index file {file_info.get('name')}: {e}")
        
        return indexed_count
    
    def get_or_index_file(self, file_id: str, file_name: str = None) -> Optional[SpreadsheetIndex]:
        """Get from cache or index on demand (lazy loading)"""
        existing = self.get_file_index(file_id)
        if existing:
            return existing
        return self.index_file(file_id, file_name)
    
    def search_and_index_matching(self, query: str, user_telegram_id: str = None) -> List[SpreadsheetIndex]:
        """
        Search for files matching query, indexing only the matching ones.
        This is lazy - we search the index first, then re-index only if needed.
        """
        # First try searching existing index
        results = self.search_files(query)
        
        # Check if any need reindexing
        for idx in results:
            needs_re, _ = self.needs_reindex(idx.file_id)
            if needs_re:
                try:
                    self.index_file(idx.file_id, idx.file_name)
                except Exception as e:
                    print(f"[ERROR] Re-index failed for {idx.file_name}: {e}")
        
        return self.search_files(query)
    
    def get_stats(self) -> Dict:
        """Get indexing statistics"""
        total = self.session.query(SpreadsheetIndex).filter_by(is_active=True).count()
        indexed_time = self.session.query(SpreadsheetIndex.last_indexed).filter_by(
            is_active=True
        ).order_by(SpreadsheetIndex.last_indexed.desc()).first()
        
        return {
            'total_indexed_files': total,
            'last_indexed_at': indexed_time[0] if indexed_time else None
        }
    
    def clear_index(self):
        """Clear all index entries (for testing/reset)"""
        self.session.query(SpreadsheetIndex).delete()
        self.session.commit()
        print("[DEBUG] SpreadsheetIndex: All entries cleared")


# Singleton instance
_index_service = None

def get_index_service() -> SpreadsheetIndexService:
    """Get or create the singleton index service"""
    global _index_service
    if _index_service is None:
        _index_service = SpreadsheetIndexService()
    return _index_service


def init_index_service() -> int:
    """
    Initialize the index service - index all files on startup.
    Returns number of files indexed.
    """
    service = get_index_service()
    print("[DEBUG] SpreadsheetIndexService: Initializing index...")
    count = service.index_all_files()
    print(f"[DEBUG] SpreadsheetIndexService: Initialized with {count} files")
    return count
