#!/usr/bin/env bash

# Fetch status
status=$(playerctl status 2>/dev/null)
if [ -z "$status" ] || [ "$status" = "Stopped" ]; then
    echo '{"text": "", "class": "stopped"}'
    exit 0
fi

raw_title=$(playerctl metadata title 2>/dev/null)
raw_artist=$(playerctl metadata artist 2>/dev/null)

title="$raw_title"
artist="$raw_artist"

# Handle YouTube / YouTube Music title formats:
# Often title is "Song Title | YouTube Music" or "Song Title - YouTube"
title=$(echo "$title" | sed -E 's/[[:space:]]*(-|\|)[[:space:]]*(YouTube Music|YouTube|SoundCloud).*$//I')
title=$(echo "$title" | sed -E 's/[[:space:]]*\|.*$//I')
title=$(echo "$title" | sed -E 's/Stream[[:space:]]+(.*)[[:space:]]+music.*/\1/I')
title=$(echo "$title" | sed -E 's/[\[\(](official|video|audio|lyrics|hd|4k|clip|slowed|reverb)[^\]\)]*[\]\)]//gI')

# If title contains " - " and artist is empty, parse Artist - Title
if [ -z "$artist" ] && [[ "$title" == *" - "* ]]; then
    artist="${title%% - *}"
    title="${title#* - }"
elif [ -z "$artist" ] && [[ "$title" == *" • "* ]]; then
    artist="${title#* • }"
    title="${title%% • *}"
fi

# Trim whitespace
title="$(echo -e "${title}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
artist="$(echo -e "${artist}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

# Fallback artist detection for well-known tracks if artist is still missing or bad
if [ -z "$artist" ] || [[ "$artist" == *"YouTube"* ]] || [[ "$artist" == *"SoundCloud"* ]]; then
    case "$title" in
        *"Blue Hair"*|*"Loving Machine"*|*"Not Allowed"*|*"Lovers Rock"*|*"Birds Dont Sing"*|*"Cigarettes out the Window"*|*"Taking What's Not Yours"*|*"Pantyhose"*|*"Hate Yourself"*|*"The Blonde"*|*"Daughter of a Cop"*|*"Her and Her Friend"*)
            artist="TV Girl"
            ;;
    esac
fi

if [ -n "$artist" ] && [ "$artist" != "$title" ]; then
    display="${artist} - ${title}"
else
    display="${title}"
fi

# Limit display length to avoid pushing the clock
if [ "${#display}" -gt 28 ]; then
    display="${display:0:26}…"
fi

icon="󰎈"
cls="playing"
if [ "$status" = "Paused" ]; then
    icon="󰏤"
    cls="paused"
fi

text="${icon}  ${display}"
tooltip="${artist} - ${title} (${status})"

printf '{"text": "%s", "tooltip": "%s", "class": "%s"}\n' "$text" "$tooltip" "$cls"
