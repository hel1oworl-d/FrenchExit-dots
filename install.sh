#!/usr/bin/env bash
set -e

DOTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/.config/dots_backup_$(date +%Y%m%d_%H%M%S)"

echo "==> French Exit Dotfiles Installer"
echo "==> Source directory: $DOTS_DIR"

# 1. Backup existing configs if present
mkdir -p "$BACKUP_DIR"
echo "==> Backing up existing configs to $BACKUP_DIR..."

configs=(cava dunst eza fastfetch fish hypr kitty waybar wofi Kvantum qt5ct qt6ct dolphinrc kdeglobals)
for item in "${configs[@]}"; do
    if [ -e "$HOME/.config/$item" ]; then
        cp -r "$HOME/.config/$item" "$BACKUP_DIR/" 2>/dev/null || true
    fi
done

# 2. Copy configs to ~/.config
echo "==> Deploying configuration files to ~/.config..."
mkdir -p "$HOME/.config"
cp -r "$DOTS_DIR/.config/"* "$HOME/.config/"

# 3. Copy user assets (~/.local/share)
if [ -d "$DOTS_DIR/.local/share" ]; then
    echo "==> Installing themes, color-schemes and icons into ~/.local/share..."
    mkdir -p "$HOME/.local/share/color-schemes"
    mkdir -p "$HOME/.local/share/icons"
    cp -r "$DOTS_DIR/.local/share/"* "$HOME/.local/share/"
    
    # Update icon cache if tool available
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        echo "==> Updating icon cache..."
        gtk-update-icon-cache -f -q "$HOME/.local/share/icons/Tela-circle-red" 2>/dev/null || true
    fi
fi

# 4. Make scripts executable
echo "==> Making scripts executable..."
find "$HOME/.config/hypr/scripts" "$HOME/.config/waybar/scripts" -type f -exec chmod +x {} + 2>/dev/null || true

# 5. Fix home path references in qt configs
sed -i "s|~|$HOME|g" "$HOME/.config/qt5ct/qt5ct.conf" 2>/dev/null || true
sed -i "s|~|$HOME|g" "$HOME/.config/qt6ct/qt6ct.conf" 2>/dev/null || true

echo ""
echo "==> All configs have been successfully installed!"
echo "==> Wallpaper location: ~/.config/hypr/wp/wp.png"
echo "==> Tip: Reload Hyprland with Super+M (or your reload shortcut) or log in again."
