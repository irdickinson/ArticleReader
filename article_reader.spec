# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect data files that packages need at runtime
datas = []
datas += collect_data_files("markdown")           # markdown templates/extensions
datas += collect_data_files("pdfminer")           # pdfminer data
datas += [("assets/icon.ico", "assets")]          # app icon

# Hidden imports that PyInstaller's static analysis may miss
hiddenimports = (
    collect_submodules("youtube_transcript_api") +
    collect_submodules("pdfminer") +
    ["PyQt6.QtPrintSupport"]   # required by Qt's print system, linked at runtime
)

a = Analysis(
    ["src/main.py"],
    pathex=["src"],            # so PyInstaller resolves `from core/ui import ...`
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "matplotlib", "scipy",
        "numpy", "pandas", "scikit_learn", "gravityai",
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
    [],
    exclude_binaries=True,
    name="ArticleReader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX can trigger Windows Defender false positives
    console=False,      # no terminal window when launched
    icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="ArticleReader",
)
