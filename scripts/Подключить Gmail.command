#!/bin/zsh
set -eu
numerom_dir="$(cd -- "$(dirname -- "$0")/.." && pwd)"
"$numerom_dir/backend/.venv/bin/python" "$numerom_dir/scripts/configure-gmail.py"
read -r "?Нажмите Enter, чтобы закрыть окно."
