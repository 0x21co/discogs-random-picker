#!/bin/bash

# Discogs Toolbox - Auto-Deployment Script for Debian
# Run as root: sudo ./deploy.sh

set -e

echo "🚀 Starting automated deployment..."

# 1. Configuration
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

echo "📍 Project Directory: $PROJECT_DIR"
echo "📍 Nginx detected at: $NGINX_BIN"

# 2. Prerequisites
echo "📦 Installing prerequisites..."
apt update && apt install -y python3-pip python3-venv curl

# 3. Virtual Environment & Dependencies
echo "🐍 Setting up Python environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
. "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

# 4. Environment Variables
if [ ! -f "$TOKEN_FILE" ]; then
    echo "⚠️  No .env file found. Please enter your Discogs Token:"
    read -r DISCOGS_TOKEN
    echo "DISCOGS_TOKEN=$DISCOGS_TOKEN" > "$TOKEN_FILE"
    echo "FLASK_SECRET_KEY=$(openssl rand -hex 16)" >> "$TOKEN_FILE"
else
    DISCOGS_TOKEN=$(grep DISCOGS_TOKEN "$TOKEN_FILE" | cut -d'=' -f2)
fi

# 5. Systemd Service
echo "⚙️  Configuring Systemd service..."
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
ExecStart=$VENV_DIR/bin/gunicorn --workers 3 --bind unix:app.sock -m 007 run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable discogs_toolbox
systemctl restart discogs_toolbox

# 6. Nginx Configuration
echo "🌐 Configuring Nginx..."
if [ "$CUSTOM_NGINX" = true ]; then
    # Add server block to custom nginx.conf if not already present
    if ! grep -q "listen $PORT" "$NGINX_CONF"; then
        # This is a basic injection before the last closing brace of the http block
        sed -i '$ d' "$NGINX_CONF" # Remove last line (usually })
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
echo "🔐 Fixing permissions..."
if [[ "$PROJECT_DIR" == /root/* ]]; then
    chmod 755 /root
fi

# Wait for socket to be created
echo "⏳ Waiting for Gunicorn to create the socket..."
for i in {1..10}; do
    if [ -S "$PROJECT_DIR/app.sock" ]; then
        chmod 666 "$PROJECT_DIR/app.sock"
        echo "✅ Socket permissions set."
        break
    fi
    sleep 1
done

if [ ! -S "$PROJECT_DIR/app.sock" ]; then
    echo "⚠️  Warning: Socket app.sock not found after 10 seconds. Check 'journalctl -u discogs_toolbox' if the app doesn't load."
fi

# 8. Firewall
if command -v ufw > /dev/null; then
    echo "🔥 Opening Firewall port $PORT..."
    ufw allow "$PORT/tcp"
fi

echo "✅ Deployment complete!"
echo "🌍 Access your app at: http://$(curl -s ifconfig.me):$PORT"
