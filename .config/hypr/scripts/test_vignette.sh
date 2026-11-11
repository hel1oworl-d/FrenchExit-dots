COVER="$HOME/.cache/hyprlock_mpris/cover.png"
BG="$HOME/.cache/hyprlock_mpris/bg.png"
if [ -f "$COVER" ]; then
    # Create gorgeous dark ambient background with deep black edges and subtle dark center
    magick "$COVER" -resize 683x384^ -gravity center -extent 683x384 -blur 0x18 -modulate 40,140 \
        \( -size 683x384 radial-gradient:rgba\(0,0,0,0.1\)-rgba\(0,0,0,0.95\) \) \
        -compose Multiply -composite -resize 1366x768 "$BG"
    file "$BG"
fi
