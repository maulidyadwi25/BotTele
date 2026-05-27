# File Access Manager - Web Admin Panel Specification

## Overview

A Flask web application for managing Telegram user permissions on Google Drive files, using the DEFEND ID ACCESS design system.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Flask (Python) |
| Database | SQLite |
| Frontend | HTML + Tailwind CSS (DEFEND ID design) |
| File Source | Google Drive API via existing `drive_service.py` |
| Authentication | Login form (session-based) |

---

## Database Schema

```sql
-- Users table (admin accounts for web panel)
CREATE TABLE admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Telegram users who can access files
CREATE TABLE telegram_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id TEXT UNIQUE NOT NULL,  -- Telegram user ID
    username TEXT,                       -- Telegram username (@xxx)
    display_name TEXT,
    status TEXT DEFAULT 'active',        -- active, suspended
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- File permissions junction table
CREATE TABLE file_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT NOT NULL,               -- Google Drive file ID
    file_name TEXT NOT NULL,
    telegram_user_id INTEGER NOT NULL,
    permission_level TEXT DEFAULT 'read', -- read, write, admin
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER,                  -- admin_users.id
    FOREIGN KEY (telegram_user_id) REFERENCES telegram_users(id),
    FOREIGN KEY (granted_by) REFERENCES admin_users(id),
    UNIQUE(file_id, telegram_user_id)
);

-- Global access toggle per user
CREATE TABLE user_global_access (
    telegram_user_id INTEGER PRIMARY KEY,
    has_global_access INTEGER DEFAULT 0,
    access_level TEXT DEFAULT 'restricted', -- global, file_specific, restricted
    FOREIGN KEY (telegram_user_id) REFERENCES telegram_users(id)
);
```

---

## Application Structure

```
bot-tele/
├── app.py                      # Flask application entry point
├── access_manager.db           # SQLite database
├── templates/
│   ├── base.html               # Base template with DEFEND ID styles
│   ├── login.html               # Login page
│   ├── dashboard.html          # Dashboard with stats
│   ├── users.html              # User management page
│   ├── files.html              # File browser with permissions
│   └── permissions.html        # Permission matrix view
├── static/
│   └── css/
│       └── defend-id.css       # Custom DEFEND ID theme overrides
├── services/
│   ├── __init__.py
│   ├── auth.py                 # Authentication service
│   ├── permission_service.py   # Permission CRUD operations
│   └── drive_service.py        # Reused from project root
├── models/
│   ├── __init__.py
│   └── database.py             # SQLite connection and setup
├── utils/
│   └── decorators.py           # Login required decorator
└── requirements.txt            # Flask + dependencies
```

---

## Pages & Features

### 1. Login Page (`/login`)
- **Design**: DEFEND ID login card with branding
- **Fields**: Administrator ID, Access Key
- **Validation**: Check against `admin_users` table
- **On success**: Redirect to dashboard, set session
- **On failure**: Show error message, keep form

### 2. Dashboard (`/dashboard`)
- **Stats cards**: Total users, Active users, Files managed, Access events
- **Quick actions**: Add user, Browse files, View logs
- **Recent activity**: Last 5 permission changes

### 3. User Management (`/users`)
- **Table columns**: Checkbox, Avatar, Name, Telegram Username, Status, Global Access toggle, Access Level, Actions
- **Features**:
  - Add new user (telegram_id, username, display_name)
  - Edit user
  - Toggle global access
  - Suspend/Activate user
  - Bulk actions (bulk grant/revoke access)
- **Search**: Filter by username or name

### 4. File Browser (`/files`)
- **Breadcrumb navigation**: Root > Folder > File
- **Table columns**: Checkbox, Icon, Name, Type, Access Status, Modified, Actions
- **Features**:
  - List files from Google Drive using `drive_service.py`
  - Click file row to manage permissions
  - Multi-select with floating action bar
  - Filter by access status
  - View toggle (list/grid)

### 5. File Permissions Modal (`/files/<file_id>/permissions`)
- **Modal dialog** overlaying file browser
- **Shows**: File name, file ID
- **User list**: Checkboxes to grant/revoke access per user
- **Permission levels**: Read (view), Write (edit), Admin (manage)
- **Actions**: Save changes, Cancel

### 6. Permission Matrix (`/permissions`)
- **Grid view**: Files as columns, Users as rows
- **Cells**: Checkbox or permission level indicator
- **Filter**: By user, by file, by status
- **Export**: CSV of permissions

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Authenticate admin |
| POST | `/api/logout` | End session |
| GET | `/api/users` | List all Telegram users |
| POST | `/api/users` | Create new Telegram user |
| PUT | `/api/users/<id>` | Update Telegram user |
| DELETE | `/api/users/<id>` | Delete Telegram user |
| GET | `/api/files` | List files from Google Drive |
| GET | `/api/files/<file_id>/permissions` | Get permissions for file |
| PUT | `/api/files/<file_id>/permissions` | Update permissions for file |
| POST | `/api/users/<id>/toggle-global` | Toggle global access |
| POST | `/api/bulk-permissions` | Bulk update permissions |

---

## Integration with bot.py

The bot will use a shared permission service:

```python
# In bot.py - check permission before showing file
def check_user_file_access(telegram_id, file_id):
    """Check if user has access to a specific file."""
    from permission_service import PermissionService
    ps = PermissionService()
    
    # Check global access first
    if ps.has_global_access(telegram_id):
        return True
    
    # Check file-specific permission
    return ps.has_file_permission(telegram_id, file_id)
```

---

## DEFEND ID Design Implementation

### Colors (from DESIGN.md)
- Primary: `#002c5f` (Security Blue)
- Secondary: `#bc0100` (Alert Red)
- Surface: `#f9f9ff`
- Surface Container: `#e9edff`
- Error: `#ba1a1a`

### Typography
- Headlines: Hanken Grotesk
- Body: Hanken Grotesk
- Labels/Mono: Geist

### Components
- Tailwind CSS via CDN (from design HTML)
- Material Symbols Outlined icons
- Custom scrollbar styling
- Floating action bar for selections
- Toggle switches for global access
- Status badges (Active, Suspended, Restricted)

---

## Security Considerations

1. **Password hashing**: Use werkzeug security for admin passwords
2. **Session management**: Flask session with secure cookie
3. **CSRF protection**: Flask-WTF forms
4. **Input validation**: All inputs sanitized
5. **Telegram user ID**: Stored as TEXT to handle large numbers

---

## Implementation Order

1. Database setup and models
2. Basic Flask app structure with login
3. User management pages (CRUD)
4. File browser integrating drive_service.py
5. Permission management modal/functionality
6. Dashboard with stats
7. Polish and testing

---

## Notes

- Reuse existing `drive_service.py` from project root
- Use `credentials.json` for Google API access
- SQLite file: `access_manager.db`
- Session secret from environment variable
