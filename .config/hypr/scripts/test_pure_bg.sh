COVER="$HOME/.cache/hyprlock_mpris/cover.png"
BG="$HOME/.cache/hyprlock_mpris/bg.png"
# Convert cover to ultra-dark atmospheric background in 0.05s
magick "$COVER" -resize 340x192^ -gravity center -extent 340x192 -blur 0x12 -fill black -colorize 82% -resize 1366x768 "$BG"
magick "$BG" -format "%[pixel:p{0,0}]\n" info:
