COVER="$HOME/.cache/hyprlock_mpris/cover.png"
BG="$HOME/.cache/hyprlock_mpris/bg.png"
if [ -f "$COVER" ]; then
    ffmpeg -y -i "$COVER" -vf "scale=170:96,boxblur=8:2,colorlevels=rimin=0.1:gimin=0.1:bimin=0.1:rimax=0.4:gimax=0.4:bimax=0.4,scale=1366:768:flags=bicubic" -frames:v 1 "$BG" 2>/dev/null
fi
