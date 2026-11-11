#!/usr/bin/env bash
# Standalone lightweight cava visualizer for waybar
PIPE="/tmp/cava_waybar.fifo"
CAVA_CFG="/tmp/cava_waybar.conf"

# Cleanup old instances
pkill -f "cava -p $CAVA_CFG" 2>/dev/null
rm -f "$PIPE" "$CAVA_CFG"

cat << 'CONF' > "$CAVA_CFG"
[general]
bars = 8
framerate = 25
[input]
method = pipewire
source = auto
[output]
method = raw
raw_target = /tmp/cava_waybar.fifo
data_format = ascii
ascii_max_range = 7
bar_delimiter = 32
CONF

mkfifo "$PIPE"
cava -p "$CAVA_CFG" >/dev/null 2>&1 &
CAVA_PID=$!

trap "kill $CAVA_PID 2>/dev/null; rm -f $PIPE $CAVA_CFG; exit 0" EXIT SIGTERM SIGINT

dict=(" " "▂" "▃" "▄" "▅" "▆" "▇" "█")

while read -r line; do
    bar=""
    for val in $line; do
        if [ "$val" -ge 0 ] && [ "$val" -le 7 ] 2>/dev/null; then
            bar+="${dict[$val]}"
        fi
    done
    if [ -n "$bar" ]; then
        echo "$bar"
    fi
done < "$PIPE"
