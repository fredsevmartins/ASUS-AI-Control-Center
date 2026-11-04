#!/usr/bin/env python3
"""Install checkout launchers only; never copy or replace the stable v5 application."""
from pathlib import Path
import datetime
import os
import shutil
import subprocess

BASE = Path(__file__).resolve().parents[1]


def exec_quote(value):
    # Desktop Entry string escaping followed by Exec argument escaping.
    value = str(value).replace('%', '%%')
    for char in ('\\', '"', '`', '$'):
        value = value.replace(char, '\\' + char)
    return '"' + value.replace('\\', '\\\\') + '"'


def entry():
    command = '/usr/bin/python3 ' + exec_quote(BASE / 'desktop_launcher.py')
    icon = str(BASE / 'desktop/mascot.png').replace('\\', '\\\\')
    return f'''[Desktop Entry]
Version=1.0
Type=Application
Name=ASUS AI Control Center
Comment=Private workstation control center
Exec={command}
Icon={icon}
Terminal=false
Categories=Utility;
StartupWMClass=asus-ai-control-center
Actions=Stop;

[Desktop Action Stop]
Name=Stop ASUS AI Control Center
Exec={command} --stop
'''


def install():
    home = Path.home()
    apps = home / '.local/share/applications'
    desktop = home / 'Desktop'
    if shutil.which('xdg-user-dir'):
        result = subprocess.run(['xdg-user-dir', 'DESKTOP'], capture_output=True, text=True, timeout=3)
        if result.returncode == 0 and result.stdout.strip():
            desktop = Path(result.stdout.strip())
    if not desktop.is_relative_to(home):
        raise RuntimeError('Desktop must be within your user account.')
    stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    for destination in (apps / 'asus-ai-control-center.desktop', desktop / 'ASUS-AI-Control-Center.desktop'):
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink():
            raise RuntimeError('Refusing to replace a symlink launcher.')
        if destination.exists():
            shutil.copy2(destination, destination.with_name(destination.name + '.backup-' + stamp))
        destination.write_text(entry())
        destination.chmod(0o755)
    if shutil.which('gio'):
        subprocess.run(['gio', 'set', str(desktop / 'ASUS-AI-Control-Center.desktop'),
                        'metadata::trusted', 'true'], check=False, capture_output=True, timeout=3)
    print('Installed ASUS AI Control Center for this user. Previous matching launchers were backed up.')
    print('If GNOME asks, right-click the desktop icon and select Allow Launching.')


if __name__ == '__main__':
    install()
