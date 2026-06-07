"""
Reset Cache and Index Utility

This script resets all caches and rebuilds the spreadsheet index.
Run this when you need to force refresh data from Google Sheets API.

Usage:
    python reset_cache_index.py          # Reset all caches and rebuild index
    python reset_cache_index.py --cache  # Reset caches only (no re-index)
    python reset_cache_index.py --index  # Rebuild index only (no cache clear)
    python reset_cache_index.py --dry    # Show what would be done without executing
"""

import argparse
import sys
import os

# Add access_manager to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Import cache modules
import gsheets_service as gs


def reset_gsheets_cache():
    """Reset all Google Sheets service caches."""
    print("[RESET] Clearing Google Sheets caches...")
    
    # Clear SHEET_METADATA_CACHE
    sheet_cache_count = len(gs.SHEET_METADATA_CACHE)
    gs.SHEET_METADATA_CACHE.clear()
    print(f"  - Cleared SHEET_METADATA_CACHE ({sheet_cache_count} entries)")
    
    # Clear SHEET_DATA_CACHE
    data_cache_count = len(gs.SHEET_DATA_CACHE)
    gs.SHEET_DATA_CACHE.clear()
    print(f"  - Cleared SHEET_DATA_CACHE ({data_cache_count} entries)")
    
    # Clear FILE_INDEX_CACHE
    file_index_count = len(gs.FILE_INDEX_CACHE)
    gs.FILE_INDEX_CACHE.clear()
    print(f"  - Cleared FILE_INDEX_CACHE ({file_index_count} entries)")
    
    print("[RESET] Google Sheets caches cleared successfully.")


def reset_bot_caches():
    """Reset bot.py in-memory caches if they exist."""
    print("[RESET] Checking bot.py caches...")
    
    # Try to import and clear bot module caches
    try:
        import bot
        if hasattr(bot, 'data_cache'):
            bot.data_cache = {"content": None, "timestamp": 0}
            print("  - Cleared bot.data_cache")
        if hasattr(bot, 'callback_cache'):
            cleared_count = len(bot.callback_cache)
            bot.callback_cache.clear()
            print(f"  - Cleared bot.callback_cache ({cleared_count} entries)")
    except ImportError:
        print("  - bot.py not found in path, skipping bot caches")
    
    # Try bot_production too
    try:
        import bot_production
        if hasattr(bot_production, 'data_cache'):
            bot_production.data_cache = {"content": None, "timestamp": 0}
            print("  - Cleared bot_production.data_cache")
        if hasattr(bot_production, 'callback_cache'):
            cleared_count = len(bot_production.callback_cache)
            bot_production.callback_cache.clear()
            print(f"  - Cleared bot_production.callback_cache ({cleared_count} entries)")
    except ImportError:
        print("  - bot_production.py not found, skipping")


def reset_spreadsheet_index():
    """Reset and rebuild the spreadsheet index in database."""
    print("[RESET] Rebuilding spreadsheet index...")
    
    from access_manager.models.bot_db import get_session, SpreadsheetIndex
    from access_manager.services.spreadsheet_index_service import SpreadsheetIndexService
    
    ctx, session = get_session()
    
    try:
        # Get current index count
        current_count = session.query(SpreadsheetIndex).filter_by(is_active=True).count()
        print(f"  - Found {current_count} indexed files in database")
        
        # Mark all existing indexes as inactive (soft delete)
        session.query(SpreadsheetIndex).filter_by(is_active=True).update(
            {"is_active": False}
        )
        session.commit()
        print(f"  - Marked {current_count} existing indexes as inactive")
        
        # Close session and create fresh service
        session.close()
        
        # Re-index all files
        index_service = SpreadsheetIndexService()
        try:
            indexed_count = index_service.index_all_files()
            print(f"[RESET] Successfully re-indexed {indexed_count} files")
        finally:
            index_service.close()
            
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to rebuild index: {e}")
        raise
    finally:
        if session:
            session.close()
        if ctx:
            ctx.pop()


def show_status():
    """Show current cache and index status without making changes."""
    print("[STATUS] Current cache and index status:\n")
    
    # Sheets caches
    print("Google Sheets Caches:")
    print(f"  - SHEET_METADATA_CACHE: {len(gs.SHEET_METADATA_CACHE)} entries")
    print(f"  - SHEET_DATA_CACHE: {len(gs.SHEET_DATA_CACHE)} entries")
    print(f"  - FILE_INDEX_CACHE: {len(gs.FILE_INDEX_CACHE)} entries")
    
    # Database index
    try:
        from access_manager.models.bot_db import get_session, SpreadsheetIndex
        ctx, session = get_session()
        active_count = session.query(SpreadsheetIndex).filter_by(is_active=True).count()
        inactive_count = session.query(SpreadsheetIndex).filter_by(is_active=False).count()
        session.close()
        ctx.pop()
        print(f"\nSpreadsheet Index (Database):")
        print(f"  - Active indexes: {active_count}")
        print(f"  - Inactive indexes: {inactive_count}")
    except Exception as e:
        print(f"\nSpreadsheet Index: Unable to query ({e})")
    
    # Bot caches
    print("\nBot Caches:")
    for bot_module in ['bot', 'bot_production']:
        try:
            mod = __import__(bot_module)
            cache_info = []
            if hasattr(mod, 'data_cache'):
                cache_info.append(f"data_cache={len(mod.data_cache)}")
            if hasattr(mod, 'callback_cache'):
                cache_info.append(f"callback_cache={len(mod.callback_cache)}")
            if cache_info:
                print(f"  - {bot_module}: {', '.join(cache_info)}")
            else:
                print(f"  - {bot_module}: no caches found")
        except ImportError:
            print(f"  - {bot_module}: not found")


def main():
    parser = argparse.ArgumentParser(
        description="Reset cache and rebuild spreadsheet index",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reset_cache_index.py         Reset everything and re-index
  python reset_cache_index.py --cache Reset caches only
  python reset_cache_index.py --index Rebuild index only  
  python reset_cache_index.py --status Show current status
        """
    )
    parser.add_argument(
        '--cache', 
        action='store_true',
        help='Reset caches only (skip re-indexing)'
    )
    parser.add_argument(
        '--index',
        action='store_true', 
        help='Rebuild index only (skip cache clear)'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status without making changes'
    )
    parser.add_argument(
        '--dry',
        action='store_true',
        help='Show what would be done without executing'
    )
    
    args = parser.parse_args()
    
    # If no specific action, show status
    if args.status:
        show_status()
        return
    
    if args.dry:
        print("[DRY RUN] Would perform the following actions:\n")
        if not args.cache:
            print("  1. Reset Google Sheets caches (SHEET_METADATA_CACHE, SHEET_DATA_CACHE, FILE_INDEX_CACHE)")
            print("  2. Reset bot.py caches (data_cache, callback_cache)")
        if not args.index:
            print("  3. Mark all existing indexes as inactive in database")
            print("  4. Re-index all spreadsheet files from Google Drive")
        print("\nUse without --dry to execute these actions.")
        return
    
    # Execute resets
    if not args.cache:
        print("\n" + "="*50)
        print("STEP 1: Clearing caches")
        print("="*50)
        reset_gsheets_cache()
        reset_bot_caches()
    
    if not args.index:
        print("\n" + "="*50)
        print("STEP 2: Rebuilding spreadsheet index")
        print("="*50)
        reset_spreadsheet_index()
    
    print("\n" + "="*50)
    print("RESET COMPLETE")
    print("="*50)
    show_status()


if __name__ == "__main__":
    main()
