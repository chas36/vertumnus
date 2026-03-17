# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None
project_root = Path.cwd()
win_icon_path = project_root / "assets" / "icons" / "app.ico"
mac_icon_path = project_root / "assets" / "icons" / "app.icns"


def optional_datas() -> list[tuple[str, str]]:
    candidates = [
        ("ui/styles.qss", "ui"),
        ("ui/styles_light.qss", "ui"),
        ("assets/icons", "assets/icons"),
        ("assets/ffmpeg/ffmpeg", "assets/ffmpeg"),
        ("assets/ffmpeg/ffprobe", "assets/ffmpeg"),
        ("assets/ffmpeg/ffmpeg.exe", "assets/ffmpeg"),
        ("assets/ffmpeg/ffprobe.exe", "assets/ffmpeg"),
    ]
    datas = []
    for relative_path, target in candidates:
        path = project_root / relative_path
        if path.exists():
            datas.append((str(path), target))
    return datas


a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=optional_datas(),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="MP4Converter",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        name="MP4Converter",
    )
    app = BUNDLE(
        coll,
        name="MP4Converter.app",
        icon=str(mac_icon_path) if mac_icon_path.exists() else None,
        bundle_identifier="com.vertumnus.mp4converter",
        info_plist={
            "CFBundleName": "MP4 Converter",
            "CFBundleDisplayName": "MP4 Converter",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "NSHighResolutionCapable": True,
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="MP4Converter",
        icon=str(win_icon_path) if win_icon_path.exists() else None,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
    )
