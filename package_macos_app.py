#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package ClashNodeX as a native macOS Application Bundle (ClashNodeX.app)
and a distributable zip archive (ClashNodeX_macOS.zip) with executable permissions.
"""

import os
import shutil
import zipfile
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "ClashNodeX.app"
APP_DIR = os.path.join(BASE_DIR, APP_NAME)
CONTENTS_DIR = os.path.join(APP_DIR, "Contents")
MACOS_DIR = os.path.join(CONTENTS_DIR, "MacOS")
RESOURCES_DIR = os.path.join(CONTENTS_DIR, "Resources")

def build_macos_app():
    print(f"[*] Building native macOS application bundle: {APP_NAME}...")

    # 1. Clean and create bundle directories
    if os.path.exists(APP_DIR):
        shutil.rmtree(APP_DIR)
    os.makedirs(MACOS_DIR, exist_ok=True)
    os.makedirs(RESOURCES_DIR, exist_ok=True)

    # 2. Generate AppIcon.icns
    icon_png = os.path.join(BASE_DIR, "app_icon.png")
    icns_path = os.path.join(RESOURCES_DIR, "AppIcon.icns")
    if os.path.exists(icon_png):
        try:
            img = Image.open(icon_png)
            img.save(icns_path, format="ICNS")
            print("  [+] AppIcon.icns created successfully.")
        except Exception as e:
            print(f"  [!] Failed to create ICNS: {e}")

    # 3. Create Contents/PkgInfo
    with open(os.path.join(CONTENTS_DIR, "PkgInfo"), "w", encoding="utf-8") as f:
        f.write("APPL????")

    # 4. Create Contents/Info.plist
    info_plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>ClashNodeX</string>
    <key>CFBundleDisplayName</key>
    <string>ClashNodeX</string>
    <key>CFBundleIdentifier</key>
    <string>com.arnold.clashnodex</string>
    <key>CFBundleVersion</key>
    <string>1.3.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.3.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleExecutable</key>
    <string>ClashNodeX</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
</dict>
</plist>
"""
    with open(os.path.join(CONTENTS_DIR, "Info.plist"), "w", encoding="utf-8", newline="\n") as f:
        f.write(info_plist_content.strip() + "\n")

    # 5. Create Contents/MacOS/ClashNodeX launcher
    launcher_script = """#!/bin/bash
# ClashNodeX macOS App Launcher
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESOURCES_DIR="$( cd "$DIR/../Resources" && pwd )"
cd "$RESOURCES_DIR"

# 1. Locate python3 on macOS
PYTHON=""
CANDIDATES=(
    "$(which python3 2>/dev/null)"
    "/opt/homebrew/bin/python3"
    "/usr/local/bin/python3"
    "/Library/Frameworks/Python.framework/Versions/Current/bin/python3"
    "/usr/bin/python3"
)

for p in "${CANDIDATES[@]}"; do
    if [ -n "$p" ] && [ -x "$p" ]; then
        PYTHON="$p"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    osascript -e 'display dialog "【ClashNodeX 运行环境提示】\\n未检测到系统安装 Python 3 环境。\\n\\n请前往官网 https://www.python.org/downloads/ 安装，或打开 Mac 终端运行 brew install python3 后重试。" with title "ClashNodeX" buttons {"好的"} default button "好的" with icon stop'
    exit 1
fi

# 2. Check essential dependencies (PyYAML, Pillow, qrcode, psutil)
$PYTHON -c "import yaml, PIL, qrcode, psutil" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    osascript -e 'display notification "首次启动正在自动安装所需依赖，请稍候..." with title "ClashNodeX" subtitle "正在准备环境"'
    $PYTHON -m pip install --quiet -r requirements.txt >/dev/null 2>&1
fi

# 3. Launch ClashNodeX GUI
exec $PYTHON gui.pyw
"""
    launcher_path = os.path.join(MACOS_DIR, "ClashNodeX")
    with open(launcher_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(launcher_script.strip() + "\n")

    # 6. Copy application code and assets to Resources
    resource_files = [
        "gui.pyw",
        "config_manager.py",
        "link_parser.py",
        "requirements.txt",
        "app_icon.png",
        "README_macOS.md",
        "run_macos.sh"
    ]
    for rf in resource_files:
        src = os.path.join(BASE_DIR, rf)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(RESOURCES_DIR, rf))
            print(f"  [+] Copied {rf} to Resources/")

    # Copy themes directory if exists
    themes_src = os.path.join(BASE_DIR, "themes")
    if os.path.exists(themes_src):
        shutil.copytree(themes_src, os.path.join(RESOURCES_DIR, "themes"), dirs_exist_ok=True)
        print("  [+] Copied themes/ to Resources/")

    print(f"[OK] macOS App Bundle created at: {APP_DIR}")

    # 7. Package into ClashNodeX_macOS.zip with Unix 0755 executable permissions
    zip_path = os.path.join(BASE_DIR, "ClashNodeX_macOS.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    print(f"[*] Packaging into distributable archive: {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(APP_DIR):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_path = os.path.relpath(abs_file, BASE_DIR)
                # Unix permissions: 0755 for executable in MacOS/, 0644 for others
                zinfo = zipfile.ZipInfo(rel_path.replace("\\", "/"))
                zinfo.compress_type = zipfile.ZIP_DEFLATED
                if "Contents/MacOS/" in rel_path.replace("\\", "/"):
                    zinfo.external_attr = 0o100755 << 16  # -rwxr-xr-x
                else:
                    zinfo.external_attr = 0o100644 << 16  # -rw-r--r--
                with open(abs_file, "rb") as f:
                    zf.writestr(zinfo, f.read())

    print(f"[OK] Distributable macOS archive created at: {zip_path}")
    return APP_DIR, zip_path

if __name__ == "__main__":
    build_macos_app()
