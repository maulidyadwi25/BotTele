# Deployment Guide - VPS dengan OS Hermes

## Prerequisites

Sebelum deploy, pastikan Anda memiliki:
- VPS dengan OS Hermes
- Domain atau subdomain yang pointing ke VPS
- Telegram Bot Token (dari @BotFather)
- File credentials.json untuk Google Sheets API
- File .env.production dengan konfigurasi yang benar

---

## Step 1: Clone/Upload Project ke VPS

```cmd
# Login ke VPS via SSH
ssh user@your-vps-ip

# Buat direktori project
mkdir -p /opt/bot-tele
cd /opt/bot-tele

# Upload semua file project (gunakan scp, rsync, atau git clone)
# Contoh dengan scp:
scp -r ./bot-tele/* user@your-vps-ip:/opt/bot-tele/
```

---

## Step 2: Setup Python Environment

```cmd
# Cek versi Python (minimal 3.9)
python3 --version

# Buat virtual environment
python3 -m venv venv

# Aktifkan virtual environment
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install aiohttp untuk webhook server
pip install aiohttp
```

---

## Step 3: Setup Environment Variables

```cmd
# Buat file .env.production
cd /opt/bot-tele
nano .env.production
```

Isi dengan konfigurasi berikut:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_PARSE_MODE=HTML
FOLDER_ID=your_google_drive_folder_id
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
WEBHOOK_MODE=true
WEBHOOK_HOST=https://your-domain.com
WEBHOOK_SECRET=your_secret_token_min_32_chars
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
```

---

## Step 4: Setup Credentials Google Sheets

```cmd
# Upload credentials.json ke VPS
scp credentials.json user@your-vps-ip:/opt/bot-tele/credentials.json

# Atur permission
chmod 600 /opt/bot-tele/credentials.json
```

---

## Step 5: Setup Reverse Proxy (Nginx/Caddy)

### Option A: Caddy (Direkomendasikan - Mudah)

```cmd
# Install Caddy
# https://caddyserver.com/docs/install

# Buat Caddyfile
nano /etc/caddy/Caddyfile
```

```
your-domain.com {
    reverse_proxy /webhook/* localhost:8080
    reverse_proxy localhost:8080
}
```

```cmd
# Restart Caddy
sudo systemctl restart caddy
```

### Option B: Nginx

```cmd
# Install Nginx
sudo apt install nginx

# Buat nginx config
sudo nano /etc/nginx/sites-available/bot-tele
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /webhook/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
    }
}
```

```cmd
# Enable config
sudo ln -s /etc/nginx/sites-available/bot-tele /etc/nginx/sites-enabled/

# Test dan restart Nginx
sudo nginx -t
sudo systemctl restart nginx
```

### SSL Certificate (Let's Encrypt)

```cmd
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Dapatkan SSL certificate
sudo certbot --nginx -d your-domain.com
```

---

## Step 6: Setup Firewall

```cmd
# Cek firewall status
sudo ufw status

# Allow port yang diperlukan
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# Enable firewall
sudo ufw enable
```

---

## Step 7: Jalankan Bot

### Test Manual (Development Mode)

```cmd
cd /opt/bot-tele
source venv/bin/activate
python bot.py
```

### Production Mode (Webhook)

```cmd
cd /opt/bot-tele
source venv/bin/activate
python bot_production.py
```

---

## Step 8: Setup Systemd Service (Auto-start)

Buat service file:

```cmd
sudo nano /etc/systemd/system/bot-tele.service
```

```ini
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/bot-tele
Environment=PATH=/opt/bot-tele/venv/bin
ExecStart=/opt/bot-tele/venv/bin/python bot_production.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```cmd
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable bot-tele

# Start service
sudo systemctl start bot-tele

# Cek status
sudo systemctl status bot-tele
```

---

## Step 9: Setup Log Rotation

```cmd
# Buat log directory
sudo mkdir -p /var/log/bot-tele

# Edit service untuk logging
sudo nano /etc/systemd/system/bot-tele.service
```

Tambahkan bagian ini di [Service]:

```ini
StandardOutput=append:/var/log/bot-tele/bot.log
StandardError=append:/var/log/bot-tele/bot.error.log
```

```cmd
# Buat logrotate config
sudo nano /etc/logrotate.d/bot-tele
```

```
/var/log/bot-tele/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

```cmd
# Restart service
sudo systemctl restart bot-tele
```

---

## Step 10: Monitoring

```cmd
# Cek logs
sudo journalctl -u bot-tele -f

# Cek log file
sudo tail -f /var/log/bot-tele/bot.log
```

---

## Troubleshooting

### Bot tidak respons
```cmd
# Cek status service
sudo systemctl status bot-tele

# Cek logs
sudo journalctl -u bot-tele -n 50
```

### Webhook tidak bekerja
```cmd
# Cek apakah webhook URL sudah benar
# Buka browser: https://api.telegram.org/bot<TOKEN>/getWebhookInfo

# Hapus webhook lama jika ada
# https://api.telegram.org/bot<TOKEN>/deleteWebhook
```

### SSL Certificate issue
```cmd
# Renew certificate
sudo certbot renew

# Cek auto-renewal
sudo certbot renew --dry-run
```

---

## Update Deployment

```cmd
# Stop service
sudo systemctl stop bot-tele

# Backup database/important files
cp -r /opt/bot-tele/data /opt/bot-tele/data.backup

# Update files
cd /opt/bot-tele
git pull  # atau upload file baru

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl start bot-tele
```

---

## Quick Reference Commands

| Action | Command |
|--------|---------|
| Start | `sudo systemctl start bot-tele` |
| Stop | `sudo systemctl stop bot-tele` |
| Restart | `sudo systemctl restart bot-tele` |
| Status | `sudo systemctl status bot-tele` |
| Logs | `sudo journalctl -u bot-tele -f` |
| Update | `cd /opt/bot-tele && git pull && sudo systemctl restart bot-tele` |
