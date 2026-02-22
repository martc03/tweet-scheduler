#!/bin/bash
set -e

# Tweet Scheduler Bot — VPS Install Script
# Run: chmod +x install.sh && ./install.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="tweet-scheduler"

echo "=== Tweet Scheduler Bot — Installer ==="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Install it with: sudo apt update && sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv "$SCRIPT_DIR/venv"
source "$SCRIPT_DIR/venv/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r "$SCRIPT_DIR/requirements.txt"
echo "Dependencies installed."

# Set up .env if it doesn't exist
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo ""
    echo "=== API Key Setup ==="
    echo "You'll need your Twitter API keys and Discord webhook URL."
    echo "Press Enter to skip any field (you can edit .env later)."
    echo ""

    read -p "Twitter API Key: " TWITTER_API_KEY
    read -p "Twitter API Secret: " TWITTER_API_SECRET
    read -p "Twitter Access Token: " TWITTER_ACCESS_TOKEN
    read -p "Twitter Access Token Secret: " TWITTER_ACCESS_SECRET
    echo ""
    read -p "Discord Webhook URL: " DISCORD_WEBHOOK_URL

    cat > "$SCRIPT_DIR/.env" << EOF
TWITTER_API_KEY=${TWITTER_API_KEY}
TWITTER_API_SECRET=${TWITTER_API_SECRET}
TWITTER_ACCESS_TOKEN=${TWITTER_ACCESS_TOKEN}
TWITTER_ACCESS_SECRET=${TWITTER_ACCESS_SECRET}
DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
EOF

    echo ""
    echo ".env file created. You can edit it later: nano $SCRIPT_DIR/.env"
else
    echo ".env already exists. Skipping API key setup."
fi

# Install systemd service
echo ""
echo "=== Systemd Service Setup ==="
read -p "Install as a systemd service? (y/n): " INSTALL_SERVICE

if [ "$INSTALL_SERVICE" = "y" ] || [ "$INSTALL_SERVICE" = "Y" ]; then
    CURRENT_USER=$(whoami)

    sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=Tweet Scheduler Bot
After=network.target

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${SCRIPT_DIR}/venv/bin/python ${SCRIPT_DIR}/bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable ${SERVICE_NAME}
    sudo systemctl start ${SERVICE_NAME}

    echo ""
    echo "Service installed and started!"
    echo ""
    echo "Useful commands:"
    echo "  sudo systemctl status ${SERVICE_NAME}    # Check status"
    echo "  sudo systemctl restart ${SERVICE_NAME}   # Restart after config change"
    echo "  sudo systemctl stop ${SERVICE_NAME}      # Stop the bot"
    echo "  journalctl -u ${SERVICE_NAME} -f         # View live logs"
else
    echo ""
    echo "Skipping service install. Run manually with:"
    echo "  cd $SCRIPT_DIR && ./venv/bin/python bot.py"
fi

echo ""
echo "=== Setup Complete ==="
echo "Edit your content:  nano $SCRIPT_DIR/tweets.csv"
echo "Edit your reminders: nano $SCRIPT_DIR/reminders.csv"
echo "Edit your schedule:  nano $SCRIPT_DIR/config.yaml"
