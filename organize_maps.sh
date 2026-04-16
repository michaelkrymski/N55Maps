#!/bin/bash

# organize_maps.sh
# Organizes scattered .bin and .log files from root into proper fuel-type subfolders
# Based on filename conventions:
#   93mapMK* → 93/
#   E30mapMK* → E30/
#   E85mapMK* → E85/
#   MKMM* → Flex/
#   Modifiedrev* → 93/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔧 Organizing N55Maps into subfolders..."

# Create subfolders if they don't exist
for folder in 93 E30 E85 Flex; do
    [ ! -d "$folder" ] && mkdir -p "$folder"
done

moved_count=0

# Move 93 octane maps
for file in 93map*.bin 93map*.log; do
    [ -e "$file" ] && [ ! -e "93/$file" ] && {
        mv "$file" "93/$file"
        echo "  → 93/$file"
        ((moved_count++))
    }
done

# Move E30 ethanol maps
for file in E30map*.bin E30map*.log; do
    [ -e "$file" ] && [ ! -e "E30/$file" ] && {
        mv "$file" "E30/$file"
        echo "  → E30/$file"
        ((moved_count++))
    }
done

# Move E85 ethanol maps
for file in E85map*.bin E85map*.log; do
    [ -e "$file" ] && [ ! -e "E85/$file" ] && {
        mv "$file" "E85/$file"
        echo "  → E85/$file"
        ((moved_count++))
    }
done

# Move Flex (MKMM) maps
for file in MKMM*.bin MKMM*.log; do
    [ -e "$file" ] && [ ! -e "Flex/$file" ] && {
        mv "$file" "Flex/$file"
        echo "  → Flex/$file"
        ((moved_count++))
    }
done

# Move Modified revisions to 93/
for file in Modified*.bin Modified*.log; do
    [ -e "$file" ] && [ ! -e "93/$file" ] && {
        mv "$file" "93/$file"
        echo "  → 93/$file"
        ((moved_count++))
    }
done

if [ $moved_count -eq 0 ]; then
    echo "✓ All files already organized!"
else
    echo "✓ Moved $moved_count files into subfolders"
fi
