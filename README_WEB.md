# Discogs Toolbox - Web GUI Deployment (Debian)

## 1. Voraussetzungen auf Debian
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx
```

## 2. Setup
```bash
# Repository klonen
git clone https://github.com/0x21co/discogs-random-picker.git
cd discogs-random-picker

# Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# ENV-Variablen setzen
cp .env.example .env  # Falls vorhanden, sonst manuell erstellen
# DISCOGS_TOKEN=dein_token_hier
```

## 3. Deployment mit Gunicorn & Systemd

### Systemd Service erstellen
Erstelle eine Datei `/etc/systemd/system/discogs_toolbox.service`:
```ini
[Unit]
Description=Gunicorn instance to serve Discogs Toolbox
After=network.target

[Service]
User=dein_user
Group=www-data
WorkingDirectory=/path/to/discogs-random-picker
Environment="PATH=/path/to/discogs-random-picker/venv/bin"
Environment="DISCOGS_TOKEN=dein_token_hier"
ExecStart=/path/to/discogs-random-picker/venv/bin/gunicorn --workers 3 --bind unix:app.sock -m 007 run:app

[Install]
WantedBy=multi-user.target
```

### Nginx Konfiguration
Erstelle eine Datei `/etc/nginx/sites-available/discogs_toolbox`:
```nginx
server {
    listen 80;
    server_name deine_domain_oder_ip;

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/discogs-random-picker/app.sock;
    }
}
```

## 4. Starten
```bash
sudo systemctl start discogs_toolbox
sudo systemctl enable discogs_toolbox
sudo ln -s /etc/nginx/sites-available/discogs_toolbox /etc/nginx/sites-enabled
sudo nginx -t && sudo systemctl restart nginx
```
