#!/bin/zsh
numerom_project="${0:A:h}"
numerom_python="${numerom_project}/backend/.service-venv/bin/python"
cd /private/tmp || exit 1
"$numerom_python" "${numerom_project}/scripts/stripe_test_environment.py"
read -r '?Нажмите Enter, чтобы закрыть окно.'
