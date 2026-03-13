#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_PATH="${VENV_PATH:-$ROOT_DIR/.venv311}"

if [[ ! -x "$VENV_PATH/bin/python" ]]; then
  echo "Не найден Python в $VENV_PATH"
  echo "Создай окружение: python3.11 -m venv .venv311"
  exit 1
fi

source "$VENV_PATH/bin/activate"

if ! command -v pyinstaller >/dev/null 2>&1; then
  pip install pyinstaller
fi

if [[ "${1:-}" != "--skip-build" ]]; then
  pyinstaller build.spec --noconfirm
fi

exec "$ROOT_DIR/dist/MP4Converter"
