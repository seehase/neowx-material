#!/bin/bash

# Patch script for skin.conf
# Reads skin_conf_patches.txt and applies key-value replacements to skin.conf

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES_FILE="$SCRIPT_DIR/skin_conf_patches.txt"
SKIN_CONF="$SCRIPT_DIR/skin.conf"

# Check if patches file exists
if [ ! -f "$PATCHES_FILE" ]; then
    echo "Error: patches.txt not found at $PATCHES_FILE"
    exit 1
fi

# Check if skin.conf exists
if [ ! -f "$SKIN_CONF" ]; then
    echo "Error: skin.conf not found at $SKIN_CONF"
    exit 1
fi

# Create backup of original skin.conf
BACKUP_FILE="${SKIN_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$SKIN_CONF" "$BACKUP_FILE"
echo "Created backup: $BACKUP_FILE"

# Read skin_conf_patches.txt and apply changes
echo "Applying patches to skin.conf..."

while IFS='=' read -r key value; do
    # Skip empty lines and comments
    if [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]]; then
        continue
    fi

    # Trim whitespace
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)

    echo "Patching: $key = $value"

    # Use sed to replace the line with the key
    # This handles the pattern "key = " (with spaces around =)
    if grep -q "^[[:space:]]*${key}[[:space:]]*=" "$SKIN_CONF"; then
        # Replace existing key
        sed -i.tmp "s|^[[:space:]]*${key}[[:space:]]*=.*|        ${key} = ${value}|" "$SKIN_CONF"
        rm "${SKIN_CONF}.tmp"
        echo "  ✓ Updated existing key: $key"
    else
        echo "  ⚠ Warning: Key '$key' not found in skin.conf"
    fi

done < "$PATCHES_FILE"

echo ""
echo "Patching complete!"
echo "Original file backed up to: $BACKUP_FILE"
echo ""
echo "Summary of changes:"

# Read patches file again and show all applied changes
while IFS='=' read -r key value; do
    # Skip empty lines and comments
    if [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]]; then
        continue
    fi

    # Trim whitespace
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)

    # Show the current value from skin.conf for this key
    if grep -q "^[[:space:]]*${key}[[:space:]]*=" "$SKIN_CONF"; then
        current_line=$(grep "^[[:space:]]*${key}[[:space:]]*=" "$SKIN_CONF")
        echo "  $current_line"
    fi

done < "$PATCHES_FILE"
