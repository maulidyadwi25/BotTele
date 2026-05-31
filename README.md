# Telegram Bot with Google Sheets & Drive Integration

Bot Telegram untuk mengelola akses file spreadsheet Google Sheets dengan sistem permission berbasis user dan AI assistant untuk query data.

## Project Overview

Sistem ini terdiri dari dua komponen utama:

1. **Telegram Bot** (`bot.py`) - Bot untuk end-user yang memungkinkan:
   - Browsing file spreadsheet dari Google Drive
   - Membaca data dari Google Sheets
   - Bertanya dalam bahasa natural tentang data menggunakan AI
   - Permission-based access control

2. **Web Admin Panel** (`access_manager/`) - Flask web app untuk administrator:
   - Mengelola user Telegram (CRUD)
   - Memberikan akses file per-user
   - Global access toggle
   - Dashboard statistik

## Architecture

```
bot-tele/
├── bot.py                      # Telegram bot (development - polling)
├── bot_production.py           # Telegram bot (production - webhook)
├── gsheets_service.py          # Google Sheets API wrapper
├── drive_service.py            # Google Drive API wrapper
├── ai_service.py               # AI provider factory (Google AI, OpenRouter, OpenAI)
├── access_manager/            # Web admin panel
│   ├── app.py                  # Flask application entry
│   ├── models/
│   │   ├── bot_db.py           # Standalone SQLAlchemy models
│   │   ├── database.py         # Flask-SQLAlchemy setup
│   │   └── user.py             # User model definitions
│   ├── routes/
│   │   ├── auth.py             # Authentication routes
│   │   ├── dashboard.py        # Dashboard routes
│   │   ├── files.py            # File browser routes
│   │   └── users.py           # User management routes
│   ├── services/
│   │   ├── permission_service.py      # Permission CRUD (Flask)
│   │   ├── bot_permission_service.py  # Permission check (bot)
│   │   └── spreadsheet_index_service.py # File indexing for caching
│   └── templates/             # HTML templates (DEFEND ID design)
└── plans/                      # Planning documents
    ├── web_admin_spec.md       # Web admin specification
    └── spreadsheet_optimization_plan.md  # Caching strategy
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Telegram Bot | python-telegram-bot |
| Web Framework | Flask |
| Database | SQLite (SQLAlchemy) |
| Google APIs | google-api-python-client, gspread |
| AI Providers | Google GenAI, OpenRouter, OpenAI Compatible |
| Frontend | HTML + Tailwind CSS |
| Design System | DEFEND ID (Custom) |

## Database Schema

### Core Tables

| Table | Description |
|-------|-------------|
| `admin_users` | Web admin accounts |
| `telegram_users` | Telegram users who can access files |
| `file_permissions` | Per-file permissions for users |
| `user_global_access` | Global access toggle per user |
| `spreadsheet_index` | Cached file/sheet metadata |

### Permission Flow

1. User sends message to bot
2. Bot checks if user is registered (`telegram_users` table)
3. Bot checks if user has `global_access` OR specific `file_permission`
4. If authorized, bot loads data and responds

## Key Features

### Telegram Bot Commands

- `/start` - Show available files/folders based on user permissions
- `/sheets` - List all sheets from all accessible files

### Bot Capabilities

- **File Browser**: Navigate folders and spreadsheet files
- **Sheet Reader**: View sheet data with actions (full data, average, total, stats)
- **AI Assistant**: Ask questions in natural language about spreadsheet data
- **Permission Enforcement**: Users only see files they have access to

### Web Admin Panel

- **Dashboard**: Stats (total users, active users, files managed)
- **User Management**: Add/edit/suspend Telegram users
- **File Browser**: Browse Google Drive files
- **Permission Matrix**: Grant/revoke file access per user

## Configuration

### Environment Variables

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_PARSE_MODE=HTML

# Google Drive
FOLDER_ID=your_google_drive_folder_id
credentials.json=path/to/service_account.json

# AI Provider (google, openrouter, openai_compatible)
AI_PROVIDER=openrouter

# Google AI
GOOGLE_API_KEY=your_key
GOOGLE_MODEL=gemini-2.5-flash

# OpenRouter
OPENROUTER_API_KEY=your_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=google/gemini-2.5-flash

# OpenAI Compatible
OPENAI_COMPATIBLE_API_KEY=your_key
OPENAI_COMPATIBLE_BASE_URL=https://api.openai.com/v1
OPENAI_COMPATIBLE_MODEL=gpt-4o-mini

# Web Admin (Flask)
SECRET_KEY=your_secret_key

# Production
WEBHOOK_MODE=true
WEBHOOK_HOST=https://your-domain.com
WEBHOOK_SECRET=your_secret_token
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run Telegram bot (development)
python bot.py

# Run Telegram bot (production with webhook)
python bot_production.py

# Run Web Admin Panel
cd access_manager
python app.py
```

### Web Admin Default Credentials

- Username: `admin`
- Password: `admin123`

## API Endpoints (Web Admin)

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

## Caching Strategy

### Google Sheets API Optimization

To prevent 429 "Quota exceeded" errors:

1. **Sheet Metadata Cache**: 10 minute TTL for sheet lists per file
2. **Sheet Data Cache**: 5 minute TTL for actual data
3. **Rate Limiting**: 1 second minimum between requests per file
4. **Exponential Backoff**: Automatic retry on 429 errors (up to 3 retries)

### Spreadsheet Index Service

Lazy indexing system that:
- Stores file/sheet metadata in SQLite
- Only re-indexes when Drive's `modifiedTime` changes
- Reduces API calls by caching metadata

## Design System (DEFEND ID)

| Color | Hex | Usage |
|-------|-----|-------|
| Primary | `#002c5f` | Security Blue - headers, buttons |
| Secondary | `#bc0100` | Alert Red - destructive actions |
| Surface | `#f9f9ff` | Background |
| Surface Container | `#e9edff` | Cards, containers |

Typography: Hanken Grotesk (headlines), Geist (labels/mono)

## Deployment

### Development

```bash
python bot.py
```

### Production (VPS)

```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure .env.production
cp .env.production.example .env.production
nano .env.production

# Run with systemd service (see DEPLOYMENT.md)
sudo systemctl start bot-tele
```

### Webhook Setup

1. Set `WEBHOOK_MODE=true` in `.env.production`
2. Configure `WEBHOOK_HOST` and `WEBHOOK_SECRET`
3. Setup reverse proxy (nginx/caddy) with SSL
4. Run `python bot_production.py`

## Important Notes

1. **Shared Database**: Both `bot.py` and web admin use the same SQLite database (`access_manager/access_manager.db`)
2. **Shortcut Support**: Bot can handle Google Drive shortcuts to spreadsheets
3. **Permission Fallback**: Users can be looked up by telegram_id OR username
4. **Thread Safety**: SQLite configured with `check_same_thread=False` for bot + web concurrent access