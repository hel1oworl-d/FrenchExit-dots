COVER="$HOME/.cache/hyprlock_mpris/cover.png"
BG="$HOME/.cache/hyprlock_mpris/bg.png"
if [ -f "$COVER" ]; then
    magick "$COVER" -resize 1366x768^ -gravity center -extent 1366x768 -blur 0x25 -modulate 40,120 "$BG"
    file "$BG"
fi
