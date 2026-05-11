#!/bin/bash

# Discogs Toolbox - Auto-Deployment Script for Debian
# Run as root: sudo ./deploy.sh

set -e

echo "[START] Starting automated deployment..."

# 1. Configuration - DYNAMIC PATH DETECTION
PROJECT_DIR=$(pwd)
VENV_DIR="$PROJECT_DIR/venv"
PORT=5000
USER=$(whoami)
TOKEN_FILE="$PROJECT_DIR/.env"

# Detect Nginx path
if [ -f "/usr/local/nginx/sbin/nginx" ]; then
    NGINX_BIN="/usr/local/nginx/sbin/nginx"
    NGINX_CONF="/usr/local/nginx/conf/nginx.conf"
    CUSTOM_NGINX=true
else
    NGINX_BIN="/usr/sbin/nginx"
    NGINX_CONF="/etc/nginx/nginx.conf"
    CUSTOM_NGINX=false
fi

echo "[INFO] Project Directory: $PROJECT_DIR"
echo "[INFO] Nginx detected at: $NGINX_BIN"

# 2. Prerequisites
echo "[SETUP] Installing prerequisites..."
apt update && apt install -y python3-pip python3-venv curl

# 3. Virtual Environment & Dependencies
echo "[PYTHON] Setting up Python environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
. "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

# 4. Environment Variables
if [ ! -f "$TOKEN_FILE" ]; then
    echo "[AUTH] No .env file found. Please enter your Discogs Token:"
    read -r DISCOGS_TOKEN
    echo "[AUTH] Please enter your default Discogs Username:"
    read -r DEFAULT_DISCOGS_USERNAME
    echo "[AUTH] Please enter a Username for the Web-GUI (Default: admin):"
    read -r WEB_USERNAME
    WEB_USERNAME=${WEB_USERNAME:-admin}
    echo "[AUTH] Please enter a Password for the Web-GUI:"
    read -r WEB_PASSWORD
    
    echo "DISCOGS_TOKEN=$DISCOGS_TOKEN" > "$TOKEN_FILE"
    echo "DEFAULT_DISCOGS_USERNAME=$DEFAULT_DISCOGS_USERNAME" >> "$TOKEN_FILE"
    echo "WEB_USERNAME=$WEB_USERNAME" >> "$TOKEN_FILE"
    echo "WEB_PASSWORD=$WEB_PASSWORD" >> "$TOKEN_FILE"
    echo "FLASK_SECRET_KEY=$(openssl rand -hex 16)" >> "$TOKEN_FILE"
else
    DISCOGS_TOKEN=$(grep DISCOGS_TOKEN "$TOKEN_FILE" | cut -d'=' -f2)
    DEFAULT_DISCOGS_USERNAME=$(grep DEFAULT_DISCOGS_USERNAME "$TOKEN_FILE" | cut -d'=' -f2 || echo "")
    WEB_USERNAME=$(grep WEB_USERNAME "$TOKEN_FILE" | cut -d'=' -f2 || echo "admin")
    WEB_PASSWORD=$(grep WEB_PASSWORD "$TOKEN_FILE" | cut -d'=' -f2 || echo "")
fi

# 5. Systemd Service
echo "[SYSTEMD] Configuring Systemd service..."
SERVICE_FILE="/etc/systemd/system/discogs_toolbox.service"
cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Gunicorn instance to serve Discogs Toolbox
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="DISCOGS_TOKEN=$DISCOGS_TOKEN"
Environment="DEFAULT_DISCOGS_USERNAME=$DEFAULT_DISCOGS_USERNAME"
Environment="WEB_USERNAME=$WEB_USERNAME"
Environment="WEB_PASSWORD=$WEB_PASSWORD"
ExecStart=$VENV_DIR/bin/gunicorn --workers 3 --timeout 120 --bind unix:app.sock --umask 000 run:app
Restart=always
UMask=000

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable discogs_toolbox
systemctl restart discogs_toolbox

# 6. Nginx Configuration
echo "[NGINX] Configuring Nginx..."
if [ "$CUSTOM_NGINX" = true ]; then
    # In custom nginx.conf, we update the proxy_pass to the NEW path if it exists
    # Or inject a new server block if none for this port exists.
    if grep -q "listen $PORT" "$NGINX_CONF"; then
        echo "[NGINX] Updating existing server block in $NGINX_CONF..."
        # Use sed to replace the proxy_pass line specifically for the socket
        sed -i "s|proxy_pass http://unix:.*app.sock;|proxy_pass http://unix:$PROJECT_DIR/app.sock;|g" "$NGINX_CONF"
    else
        echo "[NGINX] Injecting new server block into $NGINX_CONF..."
        sed -i '$ d' "$NGINX_CONF"
        cat <<EOF >> "$NGINX_CONF"
    server {
        listen $PORT;
        server_name _;
        location / {
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_pass http://unix:$PROJECT_DIR/app.sock;
        }
    }
}
EOF
    fi
    $NGINX_BIN -t
    $NGINX_BIN -s reload
else
    # Standard Debian Nginx setup
    SITE_CONF="/etc/nginx/sites-available/discogs_toolbox"
    cat <<EOF > "$SITE_CONF"
server {
    listen $PORT;
    server_name _;
    location / {
        include proxy_params;
        proxy_pass http://unix:$PROJECT_DIR/app.sock;
    }
}
EOF
    ln -sf "$SITE_CONF" /etc/nginx/sites-enabled/
    nginx -t
    systemctl restart nginx
fi

# 7. Permissions
echo "[PERM] Fixing permissions..."
case "$PROJECT_DIR" in
    /root/*)
        chmod 755 /root
        # Also ensure intermediate directories like /root/git are accessible
        CURRENT_PART="/root"
        IFS='/'
        for PART in ${PROJECT_DIR#/root/}; do
            CURRENT_PART="$CURRENT_PART/$PART"
            chmod 755 "$CURRENT_PART"
        done
        unset IFS
        ;;
esac

# Wait for socket to be created
echo "[WAIT] Waiting for Gunicorn to create the socket..."
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if [ -S "$PROJECT_DIR/app.sock" ]; then
        chmod 666 "$PROJECT_DIR/app.sock"
        echo "[SUCCESS] Socket permissions set."
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 1
done

if [ ! -S "$PROJECT_DIR/app.sock" ]; then
    echo "[WARNING] Socket app.sock not found after 10 seconds. Check 'journalctl -u discogs_toolbox' if the app doesn't load."
fi

# 8. Firewall
if command -v ufw > /dev/null; then
    echo "[FIREWALL] Opening Firewall port $PORT..."
    ufw allow "$PORT/tcp"
fi

echo "[FINISH] Deployment complete!"
echo "[URL] Access your app at: http://$(curl -s ifconfig.me):$PORT"
