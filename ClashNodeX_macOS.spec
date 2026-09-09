# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['gui.pyw'],
    pathex=[],
    binaries=[],
    datas=[('app_icon.png', '.'), ('themes', 'themes')],
    hiddenimports=['PIL', 'PIL.Image', 'PIL.ImageTk', 'qrcode', 'yaml', 'cv2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ClashNodeX',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ClashNodeX',
)

app = BUNDLE(
    coll,
    name='ClashNodeX.app',
    icon='app_icon.png',
    bundle_identifier='com.gptbridge.clashnodex',
    info_plist={
        'CFBundleName': 'ClashNodeX',
        'CFBundleDisplayName': 'ClashNodeX',
        'CFBundleGetInfoString': "ClashNodeX - Clash Verge Rev Node Manager",
        'CFBundleIdentifier': "com.gptbridge.clashnodex",
        'CFBundleVersion': "1.3.0",
        'CFBundleShortVersionString': "1.3.0",
        'NSHumanReadableCopyright': "Copyright © 2026 gpt-bridge. MIT License.",
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.15.0',
    },
)
