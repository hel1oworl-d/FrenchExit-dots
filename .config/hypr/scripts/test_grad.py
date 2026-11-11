import subprocess, time, os
COVER_FILE = os.path.expanduser("~/.cache/hyprlock_mpris/cover.png")
GRADIENT_FILE = os.path.expanduser("~/.cache/hyprlock_mpris/gradient.png")
out = subprocess.check_output(f"magick '{COVER_FILE}' -resize 50x50 -colors 2 -unique-colors txt:-", shell=True, text=True)
print(out)
