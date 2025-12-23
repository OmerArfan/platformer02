# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# List of all active folders
added_files = [
    ('audio', 'audio'),
    ('bgs', 'bgs'),
    ('char', 'char'),
    ('data', 'data'),
    ('fonts', 'fonts'),
    ('lang', 'lang'),
    ('oimgs', 'oimgs'),
    ('robots.ico', '.')
]

a = Analysis(
    ['platformer.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=['arabic_reshaper', 'bidi.algorithm'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Roboquix',  # This will be the name of your EXE
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,    # Setting this to False hides the terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='robots.ico', # Sets your custom game icon
    version='version_info.txt', 
)