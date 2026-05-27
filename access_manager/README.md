# Access Manager

File Access Management System for Telegram users with Google Drive integration.

## Features

- User Management (Telegram users)
- File Browser (Google Drive)
- Permission Management (per-file access control)
- Admin Authentication

## Setup

1. **Install dependencies:**
```bash
cd access_manager
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Set up Google Drive credentials:**
- Place your `credentials.json` in the project root
- Set `FOLDER_ID` in `.env` to your Google Drive folder ID

4. **Run the application:**
```bash
python app.py
```

5. **Login:**
- Username: `admin`
- Password: `admin123`

## Project Structure

```
access_manager/
├── app.py                  # Flask application entry point
├── models/                 # Database models
│   ├── __init__.py
│   ├── database.py
│   └── user.py
├── routes/                 # URL routes
│   ├── auth.py
│   ├── dashboard.py
│   ├── files.py
│   └── users.py
├── services/               # Business logic
│   ├── drive_integration.py
│   └── permission_service.py
├── templates/              # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── files.html
│   ├── login.html
│   └── users.html
├── utils/                  # Utilities
│   └── decorators.py
└── requirements.txt
```

## Integration with bot.py

To check user permissions from your Telegram bot:

```python
import sys
sys.path.insert(0, 'access_manager')

from services.permission_service import PermissionService

def check_access(telegram_id, file_id):
    ps = PermissionService()
    
    # Check global access first
    if ps.has_global_access(telegram_id):
        return True
    
    # Check file-specific permission
    return ps.has_file_permission(telegram_id, file_id)
```

## Design

Uses the DEFEND ID ACCESS design system:
- Colors: Primary `#002c5f`, Secondary `#bc0100`
- Typography: Hanken Grotesk, Geist
- Style: Corporate/Technical Minimalism
