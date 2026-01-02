#!/bin/bash
# JetCutter GUI 起動スクリプト
# 仮想環境のactivateに依存せず、直接Pythonを実行します

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found at $SCRIPT_DIR/.venv"
    echo "Please run: uv venv && uv pip install -e ."
    exit 1
fi

exec "$VENV_PYTHON" -m jetcutter.gui.app "$@"
