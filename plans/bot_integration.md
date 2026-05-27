# Integration Plan: Access Manager with bot.py

## Progress Checklist

- [x] 1. Create access_manager Flask web app
- [x] 2. Design DEFEND ID UI for web admin
- [x] 3. Implement user management (CRUD)
- [x] 4. Implement file browser with Google Drive
- [x] 5. Implement permission management
- [x] 6. Integrate permission checks in bot.py
- [ ] 7. Test full flow (web -> bot)
- [ ] 8. Deploy and verify

## Implementation Status

### bot.py Changes (COMPLETED)

1. **Added imports at top of bot.py:**
```python
import sys
sys.path.insert(0, 'access_manager')
from access_manager.services.permission_service import PermissionService
from access_manager.models import db
from access_manager.models.user import TelegramUser

permission_service = PermissionService()
```

2. **Auto-create users in start_command:**
```python
telegram_id = str(update.effective_user.id)
username = update.effective_user.username
display_name = update.effective_user.full_name

existing_user = TelegramUser.query.filter_by(telegram_id=telegram_id).first()
if not existing_user:
    permission_service.create_user(telegram_id, username, display_name)
```

3. **Permission check before showing file:**
```python
elif data.startswith("file_"):
    file_id = data.split("_", 1)[1]
    telegram_id = str(update.effective_user.id)
    
    if not permission_service.has_file_permission(telegram_id, file_id):
        await query.answer("Access denied. You don't have permission.", show_alert=True)
        return
```

---

## Overview

The `access_manager` module provides permission checking that can be used by `bot.py` to verify if a Telegram user has access to a specific file before showing or sharing it.

## Integration Points

### 1. Add Permission Check Before File Display

In `bot.py`, when a user requests to view a file, check permissions before displaying:

```python
# In bot.py - import at top
import sys
sys.path.insert(0, 'access_manager')

from access_manager.services.permission_service import PermissionService

ps = PermissionService()

# In handle_callback_query or sheets_command when user selects a file:
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... existing code ...
    
    elif data.startswith("file_"):
        file_id = data.split("_", 1)[1]
        telegram_id = str(update.effective_user.id)
        
        # Check permission
        if not ps.has_file_permission(telegram_id, file_id):
            await query.edit_message_text(
                "Access denied. You don't have permission to view this file.",
                parse_mode=TELEGRAM_PARSE_MODE
            )
            return
        
        # User has permission, continue with existing logic
        # ... rest of file handling code ...
```

### 2. Add Permission Check Before Folder Access

```python
# When user navigates to a folder
elif data.startswith("folder_"):
    folder_id = data.split("_", 1)[1]
    telegram_id = str(update.effective_user.id)
    
    # Option 1: Deny if no global access
    if not ps.has_global_access(telegram_id):
        await query.edit_message_text(
            "Access denied. You need global access to browse folders.",
            parse_mode=TELEGRAM_PARATE_MODE
        )
        return
    
    # Option 2: Check if user has access to ANY file in the folder
    # (more complex - requires listing files and checking each)
```

### 3. Automatic User Creation (Optional)

When a new user interacts with the bot, auto-create them in the database:

```python
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username
    display_name = update.effective_user.full_name
    
    # Auto-create user if not exists (set status to pending/active based on your flow)
    existing = TelegramUser.query.filter_by(telegram_id=telegram_id).first()
    if not existing:
        ps.create_user(telegram_id, username, display_name)
    
    # ... rest of start command ...
```

## Database Location

The SQLite database is located at:
- Development: `access_manager/access_manager.db`
- Production: Should be set via environment variable

## Important Notes

1. **Shared Database**: Both `bot.py` and the web app use the same SQLite database file.

2. **No Django/Flask conflicts**: The access_manager only uses:
   - SQLAlchemy (ORM)
   - werkzeug (password hashing)
   - No Flask app instance needed for permission checks

3. **Thread Safety**: SQLite supports concurrent reads but be careful with writes from both bot.py and web app.

4. **Telegram ID format**: Stored as STRING in database to handle large numbers.

## Environment Setup

Ensure `access_manager.db` is in the right location or set `SQLALCHEMY_DATABASE_URI` to absolute path.

## Alternative: REST API Call

Instead of direct import, the bot could call the web API:

```python
import requests

def check_permission(telegram_id, file_id):
    response = requests.get(
        f'http://localhost:5000/api/check',
        params={'telegram_id': telegram_id, 'file_id': file_id}
    )
    return response.json().get('has_access', False)
```

This approach is useful if bot.py and web app run on different servers.

## Testing the Integration

1. Run the web app: `cd access_manager && python app.py`
2. Add users via web UI
3. Assign file permissions
4. Test with Telegram bot
