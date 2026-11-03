#!/usr/bin/env bash
set -Eeuo pipefail
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m compileall -q "$BASE/server.py" "$BASE/core.py"
DEST="$HOME/.local/share/asus-ai-model-manager-v5"
mkdir -p "$DEST" "$HOME/.local/share/applications"
# Never overwrite the working v4 release. Backup existing v5 only.
if [[ -d "$DEST/web" ]]; then
  cp -a "$DEST" "$DEST.previous.$(date +%Y%m%d%H%M%S)"
fi
install -m 644 "$BASE/core.py" "$DEST/core.py"
install -m 755 "$BASE/server.py" "$DEST/server.py"
mkdir -p "$DEST/web"
cp "$BASE/web/"* "$DEST/web/"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
mkdir -p "$DESKTOP_DIR"
LAUNCHER="$HOME/.local/share/applications/asus-ai-control-center.desktop"
cat > "$LAUNCHER" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=ASUS AI Control Center v5
Comment=Private AI workstation control center
Exec=/usr/bin/python3 $DEST/server.py
Icon=utilities-system-monitor
Terminal=false
Categories=Utility;Development;
EOF
cp "$LAUNCHER" "$DESKTOP_DIR/ASUS-AI-Control-Center-v5.desktop"
chmod +x "$DESKTOP_DIR/ASUS-AI-Control-Center-v5.desktop"
gio set "$DESKTOP_DIR/ASUS-AI-Control-Center-v5.desktop" metadata::trusted true 2>/dev/null || true
printf 'Installed v5 separately from v4. Launch ASUS AI Control Center v5 from the desktop.\n'
