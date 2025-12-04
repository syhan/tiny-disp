#!/bin/bash
# Tiny Display Systemd Service Installation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "Tiny Display - Systemd Service Installation"
echo "============================================================"
echo ""

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="tiny-disp.service"
SERVICE_NAME="tiny-disp"

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}✗ This script must be run with sudo${NC}"
    echo "Usage: sudo ./install-service.sh"
    exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

echo -e "${YELLOW}Configuration:${NC}"
echo "  User: $ACTUAL_USER"
echo "  Home: $ACTUAL_HOME"
echo "  Project: $SCRIPT_DIR"
echo ""

# Prompt for plugin selection
echo -e "${YELLOW}Available plugins:${NC}"
echo "  0. World Clock"
echo "  1. Weather"
echo "  2. System Metrics"
echo "  3. System Metrics (Rotated)"
echo "  4. ZFS Pool Monitor"
echo "  5. ZFS Pool Monitor (Pages)"
echo ""

read -p "Enter plugin number or name [default: 2]: " PLUGIN_CHOICE
PLUGIN_CHOICE=${PLUGIN_CHOICE:-2}

# Map plugin choice
case "$PLUGIN_CHOICE" in
    0) PLUGIN_NAME="World Clock" ;;
    1) PLUGIN_NAME="Weather" ;;
    2) PLUGIN_NAME="System Metrics" ;;
    3) PLUGIN_NAME="System Metrics (Rotated)" ;;
    4) PLUGIN_NAME="ZFS Pool Monitor" ;;
    5) PLUGIN_NAME="ZFS Pool Monitor (Pages)" ;;
    *) PLUGIN_NAME="$PLUGIN_CHOICE" ;;
esac

echo ""
echo -e "${YELLOW}Creating service file...${NC}"

# Create temporary service file with correct paths
cat > /tmp/${SERVICE_NAME}.service << EOF
[Unit]
Description=Tiny Display Service
Documentation=https://github.com/your-repo/tiny-disp
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/main.py --plugin "$PLUGIN_NAME"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Prevent Python output buffering
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

# Copy service file to systemd directory
echo -e "${YELLOW}Installing service file...${NC}"
cp /tmp/${SERVICE_NAME}.service /etc/systemd/system/
rm /tmp/${SERVICE_NAME}.service

# Reload systemd
echo -e "${YELLOW}Reloading systemd...${NC}"
systemctl daemon-reload

# Enable service
echo -e "${YELLOW}Enabling service...${NC}"
systemctl enable ${SERVICE_NAME}.service

echo ""
echo -e "${GREEN}✓ Service installed successfully!${NC}"
echo ""
echo "Service name: ${SERVICE_NAME}"
echo "Plugin: $PLUGIN_NAME"
echo ""
echo -e "${YELLOW}Usage:${NC}"
echo "  Start:   sudo systemctl start ${SERVICE_NAME}"
echo "  Stop:    sudo systemctl stop ${SERVICE_NAME}"
echo "  Status:  sudo systemctl status ${SERVICE_NAME}"
echo "  Logs:    sudo journalctl -u ${SERVICE_NAME} -f"
echo "  Restart: sudo systemctl restart ${SERVICE_NAME}"
echo "  Disable: sudo systemctl disable ${SERVICE_NAME}"
echo ""
echo -e "${YELLOW}Auto-start on boot: ${GREEN}ENABLED${NC}"
echo ""

read -p "Start service now? [Y/n]: " START_NOW
START_NOW=${START_NOW:-Y}

if [[ "$START_NOW" =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Starting service...${NC}"
    systemctl start ${SERVICE_NAME}.service
    sleep 2

    echo ""
    echo -e "${YELLOW}Service status:${NC}"
    systemctl status ${SERVICE_NAME}.service --no-pager
    echo ""
    echo -e "${GREEN}✓ Service started!${NC}"
    echo "View logs with: sudo journalctl -u ${SERVICE_NAME} -f"
else
    echo ""
    echo -e "${YELLOW}Service not started. Start manually with:${NC}"
    echo "  sudo systemctl start ${SERVICE_NAME}"
fi

echo ""
echo "============================================================"
echo "Installation complete!"
echo "============================================================"
