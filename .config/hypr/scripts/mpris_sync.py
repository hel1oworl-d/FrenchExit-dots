#!/usr/bin/env python3
import sys
import os
import time
import subprocess
import json
import re
import math
import urllib.request
import urllib.parse

CACHE_DIR = os.path.expanduser("~/.cache/hyprlock_mpris")
os.makedirs(CACHE_DIR, exist_ok=True)

LYRICS_FILE = os.path.join(CACHE_DIR, "lyrics.json")
TRACK_INFO_FILE = os.path.join(CACHE_DIR, "track.json")
COVER_FILE = os.path.join(CACHE_DIR, "cover.png")
BLANK_COVER = os.path.join(CACHE_DIR, "blank.png")
GRADIENT_FILE = os.path.join(CACHE_DIR, "gradient.png")
BLANK_GRADIENT = os.path.join(CACHE_DIR, "blank_grad.png")
COLORS_FILE = os.path.join(CACHE_DIR, "colors.json")
APP_ID = "4EIvShl2lBPENU7rm-KbLX8hoSXqU--D6DYPWpn1j9E"

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

def clean_title_and_artist(raw_title, raw_artist):
    title = raw_title.strip()
    artist = raw_artist.strip()

    by_match = re.search(r"^(.*?)\s+by\s+(.*?)$", title, re.IGNORECASE)
    if by_match and not artist:
        title = by_match.group(1).strip()
        artist = by_match.group(2).strip()

    sc_match = re.search(r"Stream (.*?) music \|", title, re.IGNORECASE)
    if sc_match:
        artist = sc_match.group(1).strip()
        title = artist

    title = re.sub(r"\s*-\s*YouTube.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\|\s*SoundCloud.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\|.*SoundCloud.*$", "", title, flags=re.IGNORECASE)

    if " - " in title and not artist:
        parts = title.split(" - ", 1)
        artist = parts[0].strip()
        title = parts[1].strip()
    elif " — " in title and not artist:
        parts = title.split(" — ", 1)
        artist = parts[0].strip()
        title = parts[1].strip()

    clean_t = re.sub(r"[\(\[][^\)\]]*(official|video|audio|lyrics|hd|4k|clip)[^\)\]]*[\)\]]", "", title, flags=re.IGNORECASE).strip()
    if clean_t:
        title = clean_t

    return title, artist

def get_player_data():
    status = run_cmd("playerctl status 2>/dev/null")
    if not status or status.lower() == "stopped":
        return None
    
    raw_title = run_cmd("playerctl metadata title 2>/dev/null")
    raw_artist = run_cmd("playerctl metadata artist 2>/dev/null")
    album = run_cmd("playerctl metadata album 2>/dev/null")
    art_url = run_cmd("playerctl metadata mpris:artUrl 2>/dev/null")
    pos_str = run_cmd("playerctl position 2>/dev/null")
    length_str = run_cmd("playerctl metadata mpris:length 2>/dev/null")
    
    pos = float(pos_str) if pos_str else 0.0
    length = float(length_str) / 1000000.0 if length_str else 0.0

    title, artist = clean_title_and_artist(raw_title, raw_artist)
    
    return {
        "status": status,
        "title": title or "Unknown Track",
        "artist": artist or "Unknown Artist",
        "album": album or "",
        "art_url": art_url,
        "position": pos,
        "length": length
    }

def fetch_itunes_cover(title, artist):
    query = f"{artist} {title}".strip()
    if not query:
        return None
    try:
        url = "https://itunes.apple.com/search?" + urllib.parse.urlencode({
            "term": query,
            "entity": "song",
            "limit": 1
        })
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            res = json.loads(resp.read().decode())
            if res.get("resultCount", 0) > 0:
                artwork = res["results"][0].get("artworkUrl100")
                if artwork:
                    return artwork.replace("100x100bb.jpg", "600x600bb.jpg")
    except Exception:
        pass
    return None

def fetch_lyrics(title, artist, album, duration):
    try:
        params = {
            "track_name": title,
            "artist_name": artist,
        }
        if album:
            params["album_name"] = album
        if duration > 0:
            params["duration"] = int(duration)
            
        url = "https://lrclib.net/api/get?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Lrclib-App-Id": APP_ID, "User-Agent": "HyprlockMusicSync/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            if data and data.get("syncedLyrics"):
                return data
    except Exception:
        pass

    try:
        query = f"{artist} {title}".strip()
        url = "https://lrclib.net/api/search?" + urllib.parse.urlencode({"q": query})
        req = urllib.request.Request(url, headers={"Lrclib-App-Id": APP_ID, "User-Agent": "HyprlockMusicSync/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            if data and len(data) > 0:
                for item in data:
                    if item.get("syncedLyrics"):
                        return item
                return data[0]
    except Exception:
        pass
    return None

def parse_synced_lyrics(synced_lrc):
    if not synced_lrc:
        return []
    lines = []
    pattern = re.compile(r'\[(\d+):(\d+(?:\.\d+)?)\](.*)')
    for l in synced_lrc.splitlines():
        match = pattern.match(l.strip())
        if match:
            m, s, text = match.groups()
            sec = int(m) * 60 + float(s)
            t = text.strip()
            if t:
                lines.append((sec, t))
    lines.sort(key=lambda x: x[0])
    return lines

def format_time(sec):
    if sec < 0: sec = 0
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"

def is_generic_art(art_url):
    if not art_url:
        return True
    lower = art_url.lower()
    if "com.google.chrome" in lower or "chromium" in lower or "chrome" in lower or "/tmp/." in lower:
        return True
    return False

def extract_dominant_colors():
    if not os.path.exists(COVER_FILE):
        return ["#444444", "#111111"]
    try:
        out = run_cmd(f"magick '{COVER_FILE}' -resize 50x50 -colors 2 -unique-colors txt:- | grep -o '#[0-9A-Fa-f]\\{{6\\}}'")
        colors = out.splitlines() if out else []
        c1 = colors[0] if len(colors) > 0 else "#666666"
        c2 = colors[1] if len(colors) > 1 else c1
        res = [c1, c2]
        with open(COLORS_FILE, "w") as f:
            json.dump(res, f)
        return res
    except Exception:
        return ["#666666", "#222222"]

def generate_pulsing_gradient():
    colors = ["#666666", "#222222"]
    if os.path.exists(COLORS_FILE):
        try:
            with open(COLORS_FILE, "r") as f:
                colors = json.load(f)
        except Exception:
            pass
    else:
        colors = extract_dominant_colors()

    c1 = colors[0]
    c2 = colors[1] if len(colors) > 1 else c1

    t = time.time()
    # Pulse rhythm (~68 bpm / 0.9s per cycle)
    pulse = (math.sin(t * 3.5) + 1.0) / 2.0
    scale = 0.85 + pulse * 0.35  # from 0.85 to 1.20 size
    angle = int((t * 25.0) % 360)

    # Fast canvas generation (260x260) with breathing radial glow
    cmd = (
        f"magick -size 260x260 gradient:'{c1}'-'{c2}' "
        f"-distort SRT {angle} "
        f"-distort SRT '{scale} 0' "
        f"-blur 0x22 "
        f"\\( -size 260x260 radial-gradient:white-transparent \\) "
        f"-compose Multiply -composite '{GRADIENT_FILE}' 2>/dev/null"
    )
    run_cmd(cmd)

def update_cover(art_url, title, artist):
    if not os.path.exists(BLANK_COVER):
        run_cmd(f"magick -size 180x180 xc:transparent {BLANK_COVER} 2>/dev/null")
    if not os.path.exists(BLANK_GRADIENT):
        run_cmd(f"magick -size 260x260 xc:transparent {BLANK_GRADIENT} 2>/dev/null")
        
    actual_url = None
    if is_generic_art(art_url):
        actual_url = fetch_itunes_cover(title, artist)
    else:
        actual_url = art_url

    if not actual_url and is_generic_art(art_url):
        actual_url = fetch_itunes_cover(title, "")

    dest = os.path.join(CACHE_DIR, "source_cover")
    if actual_url:
        if actual_url.startswith("file://"):
            local_path = actual_url[7:]
            subprocess.run(f"magick '{local_path}' -resize 180x180^ -gravity center -extent 180x180 '{COVER_FILE}' 2>/dev/null", shell=True)
        elif actual_url.startswith("http://") or actual_url.startswith("https://"):
            try:
                req = urllib.request.Request(actual_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    with open(dest, "wb") as f:
                        f.write(resp.read())
                subprocess.run(f"magick '{dest}' -resize 180x180^ -gravity center -extent 180x180 '{COVER_FILE}' 2>/dev/null", shell=True)
            except Exception:
                pass

    if os.path.exists(COVER_FILE):
        extract_dominant_colors()
        generate_pulsing_gradient()

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    data = get_player_data()
    
    if not data:
        if mode == "cover":
            print(BLANK_COVER if os.path.exists(BLANK_COVER) else "")
        elif mode == "gradient":
            print(BLANK_GRADIENT if os.path.exists(BLANK_GRADIENT) else "")
        elif mode in ("info", "lyrics", "player"):
            print("")
        elif mode == "is_playing":
            print("false")
        return

    prev_track = {}
    if os.path.exists(TRACK_INFO_FILE):
        try:
            with open(TRACK_INFO_FILE, "r") as f:
                prev_track = json.load(f)
        except Exception:
            pass

    current_id = f"{data['artist']} - {data['title']}"
    prev_id = f"{prev_track.get('artist', '')} - {prev_track.get('title', '')}"

    if current_id != prev_id or not os.path.exists(COVER_FILE):
        update_cover(data['art_url'], data['title'], data['artist'])
        lrc_data = fetch_lyrics(data['title'], data['artist'], data['album'], data['length'])
        with open(TRACK_INFO_FILE, "w") as f:
            json.dump(data, f)
        with open(LYRICS_FILE, "w") as f:
            json.dump(lrc_data or {}, f)
    else:
        with open(TRACK_INFO_FILE, "w") as f:
            json.dump(data, f)

    if mode == "is_playing":
        print("true")
        return

    elif mode == "cover":
        if os.path.exists(COVER_FILE):
            print(COVER_FILE)
        else:
            print(BLANK_COVER if os.path.exists(BLANK_COVER) else "")
            
    elif mode == "gradient":
        generate_pulsing_gradient()
        if os.path.exists(GRADIENT_FILE):
            print(GRADIENT_FILE)
        else:
            print(BLANK_GRADIENT if os.path.exists(BLANK_GRADIENT) else "")
            
    elif mode == "player":
        title = data['title']
        if len(title) > 30:
            title = title[:28] + "…"
        artist = data['artist']
        if len(artist) > 32:
            artist = artist[:30] + "…"
            
        cur = format_time(data['position'])
        tot = format_time(data['length'])
        
        total_len = 16
        if data['length'] > 0:
            progress = min(1.0, max(0.0, data['position'] / data['length']))
            filled = int(progress * total_len)
        else:
            filled = 0
        bar = "━" * filled + "╸" + "─" * (total_len - filled)
        
        out = (
            f"<b>{title}</b>\n"
            f"<span color='#888888'>{artist}</span>\n\n"
            f"<span font_desc='monospace 10' color='#666666'>{cur} {bar} {tot}</span>"
        )
        print(out)
        
    elif mode == "lyrics":
        synced_lines = []
        if os.path.exists(LYRICS_FILE):
            try:
                with open(LYRICS_FILE, "r") as f:
                    l_data = json.load(f)
                    synced_lines = parse_synced_lyrics(l_data.get("syncedLyrics", ""))
            except Exception:
                pass
                
        if not synced_lines:
            print("")
            return
            
        cur_pos = data['position']
        active_idx = -1
        for i, (sec, text) in enumerate(synced_lines):
            if cur_pos >= sec:
                active_idx = i
            else:
                break
                
        if active_idx == -1:
            if len(synced_lines) > 0:
                print(f"<span color='#666666'><i>♪ {synced_lines[0][1]}</i></span>")
            else:
                print("")
            return
            
        cur_sec, cur_text = synced_lines[active_idx]
        next_text = synced_lines[active_idx + 1][1] if active_idx + 1 < len(synced_lines) else ""
        prev_text = synced_lines[active_idx - 1][1] if active_idx > 0 else ""

        # Smooth transition effect: compute how many seconds elapsed since line start
        time_since_line = cur_pos - cur_sec
        # Fade-in curve: within first 0.6 seconds, highlight progressively brightens
        if time_since_line < 0.2:
            main_color = "#cccccc"
            indicator = "•"
        elif time_since_line < 0.5:
            main_color = "#eeeeee"
            indicator = "●"
        else:
            main_color = "#ffffff"
            indicator = "✦"

        # 3-line karaoke / flowing aesthetic display
        lines_output = []
        if prev_text:
            lines_output.append(f"<span color='#383838' font_size='10pt'>  {prev_text}</span>")
        else:
            lines_output.append("")

        lines_output.append(f"<span color='{main_color}' font_weight='bold' font_size='13pt'>{indicator}  {cur_text}  {indicator}</span>")
        
        if next_text:
            lines_output.append(f"<span color='#666666' font_size='10pt'>  {next_text}</span>")
        else:
            lines_output.append("")

        print("\n".join(lines_output))

if __name__ == "__main__":
    main()
