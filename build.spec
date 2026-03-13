# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None
project_root = Path.cwd()
icon_path = project_root / "assets" / "icons" / "app.ico"


def optional_datas() -> list[tuple[str, str]]:
    candidates = [
        ("ui/styles.qss", "ui"),
        ("ui/styles_light.qss", "ui"),
        ("assets/icons", "assets/icons"),
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
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MP4Converter",
    icon=str(icon_path) if icon_path.exists() else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
