#!/bin/zsh
numerom_project="${0:A:h}"
numerom_python="${numerom_project}/backend/.service-venv/bin/python"
[[ -x "$numerom_python" ]] || numerom_python="${numerom_project}/backend/.venv/bin/python"
cd /private/tmp || exit 1
"$numerom_python" "${numerom_project}/scripts/start-local.py"
result=$?
if (( result != 0 )); then
  read -r '?Нажмите Enter, чтобы закрыть окно.'
fi
exit "$result"
