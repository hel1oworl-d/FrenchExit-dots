import subprocess, os, time

CACHE_DIR = os.path.expanduser("~/.cache/hyprlock_mpris")
os.makedirs(CACHE_DIR, exist_ok=True)
FRAMES_DIR = os.path.join(CACHE_DIR, "frames")
os.makedirs(FRAMES_DIR, exist_ok=True)

# Generate a 20-frame pulse animation sequence (takes ~0.5s once per track)
# Frame dimensions: 1366x768
cmd = """
magick -size 1366x768 xc:black \
  -stroke '#ffffff' -strokewidth 4 -fill none -draw 'rectangle 0,0 1365,767' \
  -blur 0x15 test_edge.png
"""
