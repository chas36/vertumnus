# Windows Build

`PyInstaller` must build the executable on Windows. A macOS build cannot produce a correct native Windows `.exe`.

## Requirements

- Windows 10/11
- Python 3.11 installed and available as `py -3.11`
- `assets/ffmpeg/ffmpeg.exe`
- `assets/ffmpeg/ffprobe.exe`

## Local Build

Run in PowerShell:

```powershell
cd path\to\vertumnus
.\build_windows.ps1
```

Or in `cmd.exe`:

```bat
build_windows.bat
```

Output:

```text
dist\MP4Converter.exe
```

## Clean Build

```powershell
.\build_windows.ps1 -Clean
```

## GitHub Actions

If the project is in GitHub, use the workflow:

```text
.github/workflows/build-windows.yml
```

It will:

1. install Python 3.11
2. install dependencies
3. run tests
4. build `dist/MP4Converter.exe`
5. upload the executable as a workflow artifact
