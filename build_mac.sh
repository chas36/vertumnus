#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -n "${VENV_PATH:-}" ]]; then
  CANDIDATES=("$VENV_PATH")
else
  CANDIDATES=("$ROOT_DIR/.venv" "$ROOT_DIR/.venv311")
fi

SELECTED_VENV=""
for candidate in "${CANDIDATES[@]}"; do
  if [[ -x "$candidate/bin/python" ]]; then
    SELECTED_VENV="$candidate"
    break
  fi
done

if [[ -z "$SELECTED_VENV" ]]; then
  echo "Не найдено рабочее виртуальное окружение."
  echo "Ожидалось одно из:"
  printf '  %s\n' "${CANDIDATES[@]}"
  exit 1
fi

source "$SELECTED_VENV/bin/activate"

if ! command -v pyinstaller >/dev/null 2>&1; then
  pip install pyinstaller
fi

pyinstaller build.spec --noconfirm

if [[ -d "$ROOT_DIR/dist/MP4Converter.app" ]]; then
  echo "Готово:"
  echo "  $ROOT_DIR/dist/MP4Converter.app"
else
  echo "PyInstaller завершился, но .app не найден."
  exit 1
fi
