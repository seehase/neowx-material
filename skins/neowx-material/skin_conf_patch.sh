#!/bin/bash

# Patch script for skin.conf
# Reads skin_conf_patches.txt and applies key-value replacements to skin.conf
# Supports section-aware key identification (e.g., Extras.Header.custom1_url)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES_FILE="$SCRIPT_DIR/skin_conf_patches.txt"
SKIN_CONF="$SCRIPT_DIR/skin.conf"

# Check if patches file exists
if [ ! -f "$PATCHES_FILE" ]; then
    echo "Error: skin_conf_patches.txt not found at $PATCHES_FILE"
    exit 1
fi

# Check if skin.conf exists
if [ ! -f "$SKIN_CONF" ]; then
    echo "Error: skin.conf not found at $SKIN_CONF"
    exit 1
fi

# Create backup of original skin.conf
BACKUP_FILE="${SKIN_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
# cp "$SKIN_CONF" "$BACKUP_FILE"
# echo "Created backup: $BACKUP_FILE"

echo "Applying patches to skin.conf..."

# Create a temporary file for the new skin.conf
TEMP_FILE=$(mktemp)

# First, read all patches and store them in a simple format
PATCHES_TEMP=$(mktemp)
while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

    # Parse Section.Subsection.key=value
    if [[ "$line" =~ ^[[:space:]]*([^=]+)=(.*)$ ]]; then
        full_key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"

        # Trim whitespace
        full_key=$(echo "$full_key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

        echo "$full_key|$value" >> "$PATCHES_TEMP"
        echo "Found patch: $full_key = $value"
    fi
done < "$PATCHES_FILE"

# Process skin.conf line by line
current_section=""
current_subsection=""
current_subsubsection=""

while IFS= read -r line || [[ -n "$line" ]]; do
    # Track current section levels
    if [[ "$line" =~ ^[[:space:]]*\[([^\]]+)\][[:space:]]*$ ]]; then
        current_section="${BASH_REMATCH[1]}"
        current_subsection=""
        current_subsubsection=""
        echo "$line" >> "$TEMP_FILE"
        continue
    elif [[ "$line" =~ ^[[:space:]]*\[\[([^\]]+)\]\][[:space:]]*$ ]]; then
        current_subsection="${BASH_REMATCH[1]}"
        current_subsubsection=""
        echo "$line" >> "$TEMP_FILE"
        continue
    elif [[ "$line" =~ ^[[:space:]]*\[\[\[([^\]]+)\]\]\][[:space:]]*$ ]]; then
        current_subsubsection="${BASH_REMATCH[1]}"
        echo "$line" >> "$TEMP_FILE"
        continue
    fi

    # Check if this line matches any patch
    line_modified=false

    while IFS='|' read -r patch_key patch_value; do
        # Parse the patch key - check for four-level format first
        if [[ "$patch_key" =~ ^([^.]+)\.([^.]+)\.([^.]+)\.([^.]+)$ ]]; then
            # Format: Section.Subsection.Subsubsection.key
            section="${BASH_REMATCH[1]}"
            subsection="${BASH_REMATCH[2]}"
            subsubsection="${BASH_REMATCH[3]}"
            key="${BASH_REMATCH[4]}"

            # Check if we're in the right section hierarchy and this line matches
            if [[ "$current_section" == "$section" ]] && [[ "$current_subsection" == "$subsection" ]] && [[ "$current_subsubsection" == "$subsubsection" ]]; then
                if [[ "$line" =~ ^[[:space:]]*${key}[[:space:]]*= ]]; then
                    echo "            $key = $patch_value" >> "$TEMP_FILE"
                    echo "  ✓ Updated: [$section][[$subsection]][[[$subsubsection]]] $key"
                    line_modified=true
                    break
                fi
            fi
        elif [[ "$patch_key" =~ ^([^.]+)\.([^.]+)\.([^.]+)$ ]]; then
            # Format: Section.Subsection.key
            section="${BASH_REMATCH[1]}"
            subsection="${BASH_REMATCH[2]}"
            key="${BASH_REMATCH[3]}"

            # Check if we're in the right section and this line matches
            if [[ "$current_section" == "$section" ]] && [[ "$current_subsection" == "$subsection" ]] && [[ -z "$current_subsubsection" ]]; then
                if [[ "$line" =~ ^[[:space:]]*${key}[[:space:]]*= ]]; then
                    echo "        $key = $patch_value" >> "$TEMP_FILE"
                    echo "  ✓ Updated: [$section][[$subsection]] $key"
                    line_modified=true
                    break
                fi
            fi
        elif [[ "$patch_key" =~ ^([^.]+)\.([^.]+)$ ]]; then
            # Format: Section.key
            section="${BASH_REMATCH[1]}"
            key="${BASH_REMATCH[2]}"

            # Check if we're in the right section and this line matches
            if [[ "$current_section" == "$section" ]] && [[ -z "$current_subsection" ]] && [[ -z "$current_subsubsection" ]]; then
                if [[ "$line" =~ ^[[:space:]]*${key}[[:space:]]*= ]]; then
                    echo "    $key = $patch_value" >> "$TEMP_FILE"
                    echo "  ✓ Updated: [$section] $key"
                    line_modified=true
                    break
                fi
            fi
        fi
    done < "$PATCHES_TEMP"

    # If line wasn't modified, keep original
    if [[ "$line_modified" == false ]]; then
        echo "$line" >> "$TEMP_FILE"
    fi

done < "$SKIN_CONF"

# Replace the original file
mv "$TEMP_FILE" "$SKIN_CONF"
rm "$PATCHES_TEMP"

echo ""
echo "Patching complete!"
#echo "Original file backed up to: $BACKUP_FILE"
echo ""
echo "Summary of applied changes:"

# Show what was applied - use a simpler approach that works on all systems
while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

    if [[ "$line" =~ ^[[:space:]]*([^=]+)=(.*)$ ]]; then
        full_key="${BASH_REMATCH[1]}"
        full_key=$(echo "$full_key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

        if [[ "$full_key" =~ ^([^.]+)\.([^.]+)\.([^.]+)\.([^.]+)$ ]]; then
            # Format: Section.Subsection.Subsubsection.key
            section="${BASH_REMATCH[1]}"
            subsection="${BASH_REMATCH[2]}"
            subsubsection="${BASH_REMATCH[3]}"
            key="${BASH_REMATCH[4]}"

            # Use a simpler approach to find the updated line
            found_line=$(grep "^[[:space:]]*${key}[[:space:]]*=" "$SKIN_CONF" | head -1)
            if [[ -n "$found_line" ]]; then
                echo "  [$section][[$subsection]][[[$subsubsection]]] $found_line"
            fi

        elif [[ "$full_key" =~ ^([^.]+)\.([^.]+)\.([^.]+)$ ]]; then
            # Format: Section.Subsection.key
            section="${BASH_REMATCH[1]}"
            subsection="${BASH_REMATCH[2]}"
            key="${BASH_REMATCH[3]}"

            # Use a simpler approach to find the updated line
            found_line=$(grep "^[[:space:]]*${key}[[:space:]]*=" "$SKIN_CONF" | head -1)
            if [[ -n "$found_line" ]]; then
                echo "  [$section][[$subsection]] $found_line"
            fi

        elif [[ "$full_key" =~ ^([^.]+)\.([^.]+)$ ]]; then
            # Format: Section.key
            section="${BASH_REMATCH[1]}"
            key="${BASH_REMATCH[2]}"

            # Use a simpler approach to find the updated line
            found_line=$(grep "^[[:space:]]*${key}[[:space:]]*=" "$SKIN_CONF" | head -1)
            if [[ -n "$found_line" ]]; then
                echo "  $found_line"
            fi
        fi
    fi
done < "$PATCHES_FILE"
