#!/usr/bin/env bash
CACHE_DIR="$HOME/.cache/hyprlock_mpris"
mkdir -p "$CACHE_DIR"

# Kill any previous daemon instance
pkill -f "mpris_daemon.py" 2>/dev/null

status=$(playerctl status 2>/dev/null)

if [ "$status" = "Playing" ] || [ "$status" = "Paused" ]; then
    # Start high-performance daemon in background
    python3 "$HOME/.config/hypr/scripts/mpris_daemon.py" &
    sleep 0.3
    cp -f "$HOME/.config/hypr/hyprlock_split.conf" "$HOME/.config/hypr/hyprlock.conf"
else
    cp -f "$HOME/.config/hypr/hyprlock_centered.conf" "$HOME/.config/hypr/hyprlock.conf"
fi
