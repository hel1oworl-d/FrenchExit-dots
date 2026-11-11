#!/usr/bin/env bash

TARGET_DIR="$HOME/Pictures/Screenshots"
mkdir -p "$TARGET_DIR"

FILE="$TARGET_DIR/Screenshot_$(date +'%Y-%m-%d_%H-%M-%S').png"

# Select region with slurp
GEOM=$(slurp 2>/dev/null)

# If selection was cancelled (e.g. Esc pressed), exit cleanly
if [ -z "$GEOM" ]; then
    exit 0
fi

# Capture selected geometry
grim -g "$GEOM" "$FILE"

# Copy to clipboard
if [ -f "$FILE" ]; then
    wl-copy --type image/png < "$FILE"
    notify-send -i "$FILE" -a "Screenshot" "Скриншот сохранён" "$(basename "$FILE")\nСкопировано в буфер"
fi
