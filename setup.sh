#!/bin/bash
#
# Presonus IO24 USB Setup Script
# 
# This script installs udev rules to allow USB access without sudo.
#
# Usage:
#   ./setup.sh         # Install udev rules
#   ./setup.sh --test  # Test current USB permissions
#   ./setup.sh --help  # Show help
#
# Run as: ./setup.sh (no sudo needed for install)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES_FILE="${SCRIPT_DIR}/udev/99-presonus-io24.rules"
RULES_DIR="/etc/udev/rules.d"
RULES_NAME="99-presonus-io24.rules"

show_help() {
    echo "Presonus IO24 USB Setup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  (none)         Install udev rules (default)"
    echo "  --test         Test current USB permissions"
    echo "  --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Install rules"
    echo "  $0 --test          # Check USB permissions"
    echo ""
}

test_permissions() {
    echo "Testing USB device permissions..."
    echo ""
    
    # Find Presonus devices
    DEVICE=$(lsusb | grep -i "presonus" | head -1)
    
    if [ -z "$DEVICE" ]; then
        echo "❌ Presonus device not found!"
        echo "   Run: lsusb | grep -i presonus"
        return 1
    fi
    
    echo "✓ Found device: $DEVICE"
    echo ""

    BUS=$(awk '{print $2}' <<< "$DEVICE")
    DEVNUM=$(awk '{print $4}' <<< "$DEVICE" | tr -d ':')
    DEVICE_PATH="/dev/bus/usb/${BUS}/${DEVNUM}"
    
    if [ -e "$DEVICE_PATH" ]; then
        echo "Target device node:"
        echo "──────────────────"
        ls -l "$DEVICE_PATH"
        echo ""
    else
        echo "⚠️  Could not resolve target device node at $DEVICE_PATH"
        echo ""
    fi
    
    # Check USB bus permissions
    USB_DEVICES=$(find /dev/bus/usb -type c 2>/dev/null | head -5)
    
    if [ -z "$USB_DEVICES" ]; then
        echo "⚠️  No USB devices found at /dev/bus/usb/"
        return 1
    fi
    
    echo "Sample USB device permissions:"
    echo "─────────────────────────────"
    ls -l $USB_DEVICES | while read line; do
        echo "  $line"
    done
    echo ""
    
    # Check if rules file exists
    if [ -f "$RULES_FILE" ]; then
        echo "✓ Udev rules file exists: $RULES_FILE"
    else
        echo "⚠️  Udev rules file not found: $RULES_FILE"
    fi
    
    # Check if rules installed
    INSTALLED_RULES=$(ls -la "$RULES_DIR/$RULES_NAME" 2>/dev/null || true)
    if [ -n "$INSTALLED_RULES" ]; then
        echo "✓ Udev rules installed at $RULES_DIR/$RULES_NAME"
    else
        echo "⚠️  Udev rules NOT installed yet"
        echo "   Run: ./setup.sh"
    fi
    
    # Check logind/uaccess fallback and group membership
    USER=$(whoami)
    if getent group plug >/dev/null 2>&1; then
        if groups | grep -q '\bplug\b'; then
            echo "✓ User '$USER' is in plug group"
        else
            echo "⚠️  User '$USER' is NOT in plug group"
        fi
    else
        echo "ℹ️  System has no 'plug' group; uaccess-based rule will be used instead"
    fi
}

install_rules() {
    echo "Installing Presonus IO24 udev rules..."
    echo ""
    
    # Check if rules file exists
    if [ ! -f "$RULES_FILE" ]; then
        echo "❌ Rules file not found: $RULES_FILE"
        exit 1
    fi
    
    echo "Rules file: $RULES_FILE"
    
    # Check for sudo
    if [ "$(id -u)" -ne 0 ]; then
        echo "⚠️  Running as non-root user"
        echo "   Will use sudo to install rules"
        echo ""
    fi
    
    run_root() {
        if [ "$(id -u)" -eq 0 ]; then
            "$@"
            return
        fi

        if sudo -n true 2>/dev/null; then
            sudo "$@"
            return
        fi

        echo "❌ Root access is required to install udev rules."
        echo ""
        echo "Run these commands in a terminal where sudo can prompt you:"
        echo "  sudo cp \"$RULES_FILE\" \"${RULES_DIR}/${RULES_NAME}\""
        echo "  sudo udevadm control --reload-rules"
        echo "  sudo udevadm trigger --attr-match=idVendor=194f --attr-match=idProduct=0422"
        echo ""
        echo "Then unplug/replug the device and run:"
        echo "  ./setup.sh --test"
        exit 1
    }

    # Copy rules file
    run_root cp "$RULES_FILE" "${RULES_DIR}/${RULES_NAME}"
    
    echo "✓ Copied rules to ${RULES_DIR}/${RULES_NAME}"
    
    # Reload udev rules
    run_root udevadm control --reload-rules
    echo "✓ Reloading udev rules"
    
    # Trigger events
    run_root udevadm trigger --attr-match=idVendor=194f --attr-match=idProduct=0422
    echo "✓ Triggering udev events"
    
    echo ""
    echo "✅ Udev rules installed successfully!"
    echo ""
    echo "Testing the setup:"
    echo "  ./setup.sh --test"
    echo "  python3 - <<'PY'"
    echo "  from presonus.device import PresonusDevice"
    echo "  print(len(PresonusDevice.find_devices()))"
    echo "  PY"
    echo ""
    echo "If access still fails, unplug/replug the device or run:"
    echo "  sudo udevadm trigger --attr-match=idVendor=194f --attr-match=idProduct=0422"
}

# Parse arguments
if [ $# -eq 0 ]; then
    # Default action: install
    install_rules
    exit 0
fi

case "$1" in
    --help|-h)
        show_help
        exit 0
        ;;
    --test)
        test_permissions
        exit $?
        ;;
    *)
        echo "Unknown option: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
