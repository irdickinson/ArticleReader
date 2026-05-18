# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

block_cipher = None

# Collect data files + binaries for packages that need them at runtime
datas, binaries, hiddenimports = [], [], []

datas += collect_data_files("markdown")
datas += collect_data_files("pdfminer")
datas += [("assets/icon.ico", "assets")]

# sounddevice bundles the PortAudio DLL; collect_all handles the binary
_d, _b, _h = collect_all("sounddevice")
datas += _d; binaries += _b; hiddenimports += _h

# miniaudio has a compiled C extension
_d, _b, _h = collect_all("miniaudio")
datas += _d; binaries += _b; hiddenimports += _h

# numpy is required by the TTS audio pipeline
_d, _b, _h = collect_all("numpy")
datas += _d; binaries += _b; hiddenimports += _h

# edge-tts is pure Python but has nested submodules
hiddenimports += collect_submodules("edge_tts")
hiddenimports += collect_submodules("aiohttp")

# Other hidden imports PyInstaller's static analysis may miss
hiddenimports += (
    collect_submodules("youtube_transcript_api") +
    collect_submodules("pdfminer") +
    ["PyQt6.QtPrintSupport"]
)

a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "matplotlib", "scipy",
        "pandas", "scikit_learn", "gravityai",
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
    upx=False,
    console=False,
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
