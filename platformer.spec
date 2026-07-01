# -*- mode: python ; coding: utf-8 -*-
import sys
block_cipher = None
# List of all active folders
added_files = [
    ('assets', 'assets'),
    ('cleobo', 'cleobo'),
]
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=['arabic_reshaper', 'bidi.algorithm', "requests", "PIL"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'setuptools', 
        'pkg_resources', 
        'distutils', 
        'doctest', 
        'pdb', 
        'PIL.SpiderImagePlugin',   
        'PIL.ImageTk',        
        'PIL.ImageQt',             
        'PIL.ImageFilter',         
        'PIL.ImageDraw',           
        'PIL.ImageFont',           
        'PIL.OleFileIO',           
        'PIL.PdfParser',           
        'PIL.PyAccess',           
        'bidi.tests',
        'bidi.bin',
        'email.generator',
        'ftplib', 
        'PIL.PdfImagePlugin', 
        'PIL.EpsImagePlugin', 
        'PIL.TiffImagePlugin', 
        'PIL.PcxImagePlugin', 
        'PIL.XpmImagePlugin', 
        'PIL.MpegImagePlugin',
        'PIL.FpxImagePlugin',
        'PIL.Hdf5StubImagePlugin',
        'tracemalloc', 
    ],
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
    # Logic for OS-specific naming
    name='Roboquix' if sys.platform != 'win32' else 'Roboquix.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Logic for OS-specific assets
    icon='assets/imgs/icons/robots.ico' if sys.platform == 'win32' else None,
    version='version_info.txt' if sys.platform == 'win32' else None,
)
 
