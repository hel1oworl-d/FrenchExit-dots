# 🌹 French Exit (TV Girl) Dotfiles

A cohesive, aesthetic Hyprland desktop environment themed around **TV Girl's** iconic debut album *French Exit* (2014) — featuring deep graphite/black backgrounds, crimson and magenta accents, custom icons, and matched application styling.

---

## 🎨 Palette & Style
- **Accents:** Crimson Red (`#D82845`, `#DD4A4A`, `#A43536`) & Muted Rose (`#F47189`)
- **Backgrounds:** Deep warm graphite (`#141113`, `#181416`, `#221B1E`)
- **Text & UI:** Off-white & soft cream (`#EBE6E6`, `#F2D4D4`)

---

## 📦 What's Included
- **Hyprland:** Configured via `hyprland.lua` with matching active/inactive border gradients and shadow profiles.
- **Hyprpaper:** Dynamic wallpaper management (`~/.config/hypr/wp/wp.png`), splash text disabled.
- **Hyprlock:** Lockscreen layouts with static & MPRIS player integration.
- **Waybar:** Minimalist top bar with custom MPRIS track info, CAVA visualizer, and custom modules.
- **Wofi:** Matching application launcher.
- **Kitty:** Terminal profile matching the colorway.
- **Dolphin & KDE:** Full Kvantum theme, `FrenchExit.colors` color scheme, and custom `Tela-circle-red` icon pack.
- **Cava / Dunst / Fastfetch / Fish:** Matched styles and configs.

---

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/FrenchExit-dots.git ~/FrenchExit-dots
cd ~/FrenchExit-dots
```

### 2. Run the installer
```bash
chmod +x install.sh
./install.sh
```

The script automatically:
1. Backs up your existing configs to `~/.config/dots_backup_<timestamp>/`.
2. Deploys configs to `~/.config/`.
3. Deploys custom color schemes and the `Tela-circle-red` icon theme to `~/.local/share/`.
4. Fixes executable permissions for scripts.
