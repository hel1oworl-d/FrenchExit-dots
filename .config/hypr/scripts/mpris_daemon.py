#!/usr/bin/env python3
import sys
import os
import time
import subprocess
import json
import re
import urllib.request
import urllib.parse
import threading

CACHE_DIR = os.path.expanduser("~/.cache/hyprlock_mpris")
os.makedirs(CACHE_DIR, exist_ok=True)

LYRICS_FILE = os.path.join(CACHE_DIR, "lyrics.json")
COVER_FILE = os.path.join(CACHE_DIR, "cover.png")
BLANK_COVER = os.path.join(CACHE_DIR, "blank.png")
BG_FILE = os.path.join(CACHE_DIR, "bg.png")
TEXT_TRACK_FILE = os.path.join(CACHE_DIR, "track_title.txt")
TEXT_BAR_FILE = os.path.join(CACHE_DIR, "timeline_bar.txt")
TEXT_LYRICS_FILE = os.path.join(CACHE_DIR, "lyrics_text.txt")

APP_ID = "4EIvShl2lBPENU7rm-KbLX8hoSXqU--D6DYPWpn1j9E"

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

def clean_title_and_artist(raw_title, raw_artist):
    title = (raw_title or "").strip()
    artist = (raw_artist or "").strip()

    by_match = re.search(r"^(.*?)\s+by\s+(.*?)$", title, re.IGNORECASE)
    if by_match:
        title = by_match.group(1).strip()
        uploader = by_match.group(2).strip()
        if not artist or "SoundCloud" in artist or "system" in artist:
            artist = uploader

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

    clean_t = re.sub(r"[\(\[][^\)\]]*(official|video|audio|lyrics|hd|4k|clip|slowed|reverb)[^\)\]]*[\)\]]", "", title, flags=re.IGNORECASE).strip()
    if clean_t:
        title = clean_t

    return title, artist

def fetch_cover_deezer(title, artist):
    queries = [
        f"{artist} {title}".strip(),
        f"{title}".strip()
    ]
    for q in queries:
        if not q: continue
        try:
            url = "https://api.deezer.com/search?" + urllib.parse.urlencode({"q": q})
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                res = json.loads(resp.read().decode())
                data = res.get("data", [])
                if data and len(data) > 0:
                    cov = data[0].get("album", {}).get("cover_big")
                    if cov:
                        return cov
        except Exception:
            pass
    return None

def fetch_lyrics(title, artist, album, duration):
    queries = [
        {"track_name": title, "artist_name": artist},
        {"track_name": title}
    ]
    for p in queries:
        try:
            url = "https://lrclib.net/api/get?" + urllib.parse.urlencode(p)
            req = urllib.request.Request(url, headers={"Lrclib-App-Id": APP_ID, "User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
                if data and data.get("syncedLyrics"):
                    return data
        except Exception:
            pass

    try:
        url = "https://lrclib.net/api/search?" + urllib.parse.urlencode({"q": f"{artist} {title}".strip()})
        req = urllib.request.Request(url, headers={"Lrclib-App-Id": APP_ID, "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=2) as resp:
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

def render_dark_background(cover_path):
    if not os.path.exists(cover_path):
        return
    # Dark Vanta-style tinted background (85% black overlay, never bright/white)
    cmd = (
        f"magick '{cover_path}' -resize 340x192^ -gravity center -extent 340x192 "
        f"-blur 0x14 -fill black -colorize 82% -resize 1366x768 '{BG_FILE}'"
    )
    subprocess.run(cmd, shell=True)

def async_track_update(art_url, title, artist, album, length, callback):
    # Fetch clean cover using Deezer search
    actual_url = None
    if is_generic_art(art_url):
        actual_url = fetch_cover_deezer(title, artist)
    else:
        actual_url = art_url

    if not actual_url and is_generic_art(art_url):
        actual_url = fetch_cover_deezer(title, "")

    dest = os.path.join(CACHE_DIR, "source_cover")
    if actual_url:
        if actual_url.startswith("file://"):
            local_path = actual_url[7:]
            subprocess.run(f"magick '{local_path}' -resize 180x180^ -gravity center -extent 180x180 '{COVER_FILE}'", shell=True)
        elif actual_url.startswith("http://") or actual_url.startswith("https://"):
            try:
                req = urllib.request.Request(actual_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    with open(dest, "wb") as f:
                        f.write(resp.read())
                subprocess.run(f"magick '{dest}' -resize 180x180^ -gravity center -extent 180x180 '{COVER_FILE}'", shell=True)
            except Exception:
                pass

    if os.path.exists(COVER_FILE):
        render_dark_background(COVER_FILE)

    lrc_data = fetch_lyrics(title, artist, album, length)
    parsed_lrc = parse_synced_lyrics(lrc_data.get("syncedLyrics", "") if lrc_data else "")
    callback(parsed_lrc)

def main_loop():
    current_track_id = ""
    lyrics_lines = []
    is_fetching = False

    def on_lyrics_loaded(lines):
        nonlocal lyrics_lines, is_fetching
        lyrics_lines = lines
        is_fetching = False

    while True:
        status = run_cmd("playerctl status 2>/dev/null")
        if not status or status.lower() == "stopped":
            with open(TEXT_TRACK_FILE, "w") as f: f.write("")
            with open(TEXT_BAR_FILE, "w") as f: f.write("")
            with open(TEXT_LYRICS_FILE, "w") as f: f.write("")
            time.sleep(0.5)
            continue

        raw_title = run_cmd("playerctl metadata title 2>/dev/null")
        raw_artist = run_cmd("playerctl metadata artist 2>/dev/null")
        album = run_cmd("playerctl metadata album 2>/dev/null")
        art_url = run_cmd("playerctl metadata mpris:artUrl 2>/dev/null")
        pos_str = run_cmd("playerctl position 2>/dev/null")
        length_str = run_cmd("playerctl metadata mpris:length 2>/dev/null")

        pos = float(pos_str) if pos_str else 0.0
        length = float(length_str) / 1000000.0 if length_str else 0.0

        title, artist = clean_title_and_artist(raw_title, raw_artist)
        track_id = f"{artist} - {title}"

        disp_title = title if len(title) <= 30 else title[:28] + "…"
        disp_artist = artist if len(artist) <= 32 else artist[:30] + "…"
        track_text = f"<b>{disp_title}</b>\n<span color='#888888'>{disp_artist}</span>"
        with open(TEXT_TRACK_FILE, "w") as f:
            f.write(track_text)

        cur_t = format_time(pos)
        tot_t = format_time(length)
        total_len = 16
        if length > 0:
            progress = min(1.0, max(0.0, pos / length))
            filled = int(progress * total_len)
        else:
            filled = 0
        bar = "━" * filled + "╸" + "─" * (total_len - filled)
        bar_text = f"{cur_t}  {bar}  {tot_t}"
        with open(TEXT_BAR_FILE, "w") as f:
            f.write(bar_text)

        if (track_id != current_track_id or not os.path.exists(COVER_FILE) or not os.path.exists(BG_FILE)) and not is_fetching:
            current_track_id = track_id
            lyrics_lines = []
            is_fetching = True
            t = threading.Thread(target=async_track_update, args=(art_url, title, artist, album, length, on_lyrics_loaded))
            t.daemon = True
            t.start()

        if lyrics_lines:
            active_idx = -1
            for i, (sec, text) in enumerate(lyrics_lines):
                if pos >= sec:
                    active_idx = i
                else:
                    break

            if active_idx != -1:
                cur_sec, cur_text = lyrics_lines[active_idx]
                prev_text = lyrics_lines[active_idx - 1][1] if active_idx > 0 else ""
                next_text = lyrics_lines[active_idx + 1][1] if active_idx + 1 < len(lyrics_lines) else ""

                time_since_line = pos - cur_sec
                if time_since_line < 0.2:
                    main_col = "#cccccc"
                    bullet = "•"
                elif time_since_line < 0.4:
                    main_col = "#eeeeee"
                    bullet = "●"
                else:
                    main_col = "#ffffff"
                    bullet = "✦"

                l_out = []
                if prev_text:
                    l_out.append(f"<span color='#383838' font_size='10pt'>  {prev_text}</span>")
                else:
                    l_out.append("")

                l_out.append(f"<span color='{main_col}' font_weight='bold' font_size='13pt'>{bullet}  {cur_text}  {bullet}</span>")

                if next_text:
                    l_out.append(f"<span color='#666666' font_size='10pt'>  {next_text}</span>")
                else:
                    l_out.append("")

                lyrics_text = "\n".join(l_out)
            else:
                lyrics_text = f"<span color='#555555'><i>♪ {lyrics_lines[0][1]}</i></span>"
        else:
            lyrics_text = ""

        with open(TEXT_LYRICS_FILE, "w") as f:
            f.write(lyrics_text)

        time.sleep(0.08)

if __name__ == "__main__":
    main_loop()
