#!/bin/bash

# save_map.sh
# Saves a new tuning revision, auto-detects next version number, updates symlinks
# Usage: ./save_map.sh <path_to_new.bin> [commit message]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <path_to_new.bin> [commit message]"
    echo "Example: $0 ~/TunerPro/93mapMK30.bin 'New 93 octane tune - improved mid-range'"
    exit 1
fi

SOURCE_BIN="$1"
COMMIT_MSG="${2:-Auto-saved new map revision}"

if [ ! -f "$SOURCE_BIN" ]; then
    echo "❌ Error: File not found: $SOURCE_BIN"
    exit 1
fi

BASENAME=$(basename "$SOURCE_BIN")

# Detect fuel type and extract current number/variant
FUEL_TYPE=""
CURRENT_VARIANT=""
DEST_DIR=""

if [[ "$BASENAME" =~ ^93map(.*)\.bin$ ]]; then
    FUEL_TYPE="93"
    CURRENT_VARIANT="${BASH_REMATCH[1]}"
    DEST_DIR="93"
elif [[ "$BASENAME" =~ ^E30map(.*)\.bin$ ]]; then
    FUEL_TYPE="E30"
    CURRENT_VARIANT="${BASH_REMATCH[1]}"
    DEST_DIR="E30"
elif [[ "$BASENAME" =~ ^E85map(.*)\.bin$ ]]; then
    FUEL_TYPE="E85"
    CURRENT_VARIANT="${BASH_REMATCH[1]}"
    DEST_DIR="E85"
elif [[ "$BASENAME" =~ ^MKMM(.*)\.bin$ ]]; then
    FUEL_TYPE="Flex"
    CURRENT_VARIANT="${BASH_REMATCH[1]}"
    DEST_DIR="Flex"
elif [[ "$BASENAME" =~ ^Modified(.*)\.bin$ ]]; then
    FUEL_TYPE="Modified"
    CURRENT_VARIANT="${BASH_REMATCH[1]}"
    DEST_DIR="93"
else
    echo "❌ Error: Unrecognized filename format: $BASENAME"
    echo "Expected: 93map*, E30map*, E85map*, MKMM*, or Modified*"
    exit 1
fi

echo "📦 Saving new $FUEL_TYPE map revision..."
echo "   Current variant: $CURRENT_VARIANT"

# Find next revision number
find_next_revision() {
    local pattern="$1"
    local dir="$2"

    local nums=($(ls "$dir"/ 2>/dev/null | grep -oE "$pattern" | sort -V | tail -20))

    if [ ${#nums[@]} -eq 0 ]; then
        echo "1"
        return
    fi

    # Extract the number from the last match and increment
    local last=${nums[-1]}
    local next=$((last + 1))
    echo "$next"
}

if [ "$FUEL_TYPE" = "93" ]; then
    if [[ "$CURRENT_VARIANT" =~ ^MK([0-9]+)(.*)$ ]]; then
        NEXT_REV=$(find_next_revision "MK[0-9]+" "$DEST_DIR")
        NEW_BASENAME="93mapMK${NEXT_REV}${BASH_REMATCH[2]}.bin"
    elif [[ "$CURRENT_VARIANT" == "F"* ]]; then
        NEW_BASENAME="93mapMKF${CURRENT_VARIANT:1}.bin"
    else
        NEW_BASENAME="93mapMK1.bin"
    fi
elif [ "$FUEL_TYPE" = "E30" ]; then
    NEXT_REV=$(find_next_revision "MK[0-9]+" "$DEST_DIR")
    if [[ "$CURRENT_VARIANT" =~ (.*)(\(.*\))$ ]]; then
        NEW_BASENAME="E30mapMK${NEXT_REV}${BASH_REMATCH[2]}.bin"
    else
        NEW_BASENAME="E30mapMK${NEXT_REV}(PD).bin"
    fi
elif [ "$FUEL_TYPE" = "E85" ]; then
    NEXT_REV=$(find_next_revision "MK[0-9]+" "$DEST_DIR")
    if [[ "$CURRENT_VARIANT" =~ (.*)(\(.*\))$ ]]; then
        NEW_BASENAME="E85mapMK${NEXT_REV}${BASH_REMATCH[2]}.bin"
    else
        NEW_BASENAME="E85mapMK${NEXT_REV}(PD3M).bin"
    fi
elif [ "$FUEL_TYPE" = "Flex" ]; then
    # For MKMM maps, use the variant as-is (e.g., 0.1, 0.2, 93E40)
    NEW_BASENAME="MKMM($CURRENT_VARIANT).bin"
elif [ "$FUEL_TYPE" = "Modified" ]; then
    NEXT_REV=$(find_next_revision "rev[0-9]+" "$DEST_DIR")
    NEW_BASENAME="Modifiedrev${NEXT_REV}.bin"
fi

# Remove old _LATEST symlinks in root for this fuel type
if [ -L "${FUEL_TYPE}_LATEST" ]; then
    rm "${FUEL_TYPE}_LATEST"
fi
if [ -L "${FUEL_TYPE}_LATEST.bin" ]; then
    rm "${FUEL_TYPE}_LATEST.bin"
fi

# Remove old _LATEST files in the subfolder
for old_latest in "$DEST_DIR"/*_LATEST.bin "$DEST_DIR"/*_LATEST.log; do
    [ -f "$old_latest" ] && rm "$old_latest"
done

# Copy new file and create _LATEST variant
NEW_FILE="$DEST_DIR/$NEW_BASENAME"
NEW_LATEST="${NEW_FILE%.bin}_LATEST.bin"

if [ -f "$NEW_FILE" ]; then
    echo "⚠️  $NEW_FILE already exists, overwriting..."
fi

cp "$SOURCE_BIN" "$NEW_FILE"
ln -sf "$(basename "$NEW_LATEST")" "$NEW_LATEST" 2>/dev/null || cp "$NEW_FILE" "$NEW_LATEST"

# Create optional log file
NEW_LOG="${NEW_FILE%.bin}.log"
if [ ! -f "$NEW_LOG" ]; then
    echo "Saved: $(date)" > "$NEW_LOG"
fi

echo "✓ Saved: $NEW_FILE"
echo "✓ Latest: $NEW_LATEST"

# Git operations (optional, silent if not available)
if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
    read -p "Commit and push to GitHub? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add "$DEST_DIR/$NEW_BASENAME" "$DEST_DIR/$NEW_BASENAME%.bin.log" "$NEW_LATEST" "$NEW_LOG" 2>/dev/null || true
        git commit -m "$COMMIT_MSG" --quiet 2>/dev/null || true
        git push --quiet 2>/dev/null || echo "⚠️  Git push failed (check remote)"
        echo "✓ Committed and pushed"
    fi
fi

# Silently refresh symlinks
bash "refresh_shortcuts.sh" --auto 2>/dev/null || true

echo "✓ Done!"
