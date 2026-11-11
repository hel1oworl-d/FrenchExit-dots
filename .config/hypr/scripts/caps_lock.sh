#!/usr/bin/env bash
state=$(hyprctl devices -j 2>/dev/null | jq -r '.keyboards[] | select(.main == true) | .capsLock' 2>/dev/null)
if [ "$state" = "true" ]; then
    echo "<span color='#ffffff' font_weight='bold'>󰬈 CAPS ON</span>"
else
    echo ""
fi
