#!/usr/bin/env bash
set -e

python3 -m venv .venv --system-site-packages
. ./.venv/bin/activate

pip install --upgrade pip
export AIRFLOW_HOME="$(mktemp -d)"

airflow_config="$AIRFLOW_HOME/airflow.cfg"
echo "[core]" >> "$airflow_config"
echo "load_examples = False" >> "$airflow_config"
echo Using "AIRFLOW_HOME=$AIRFLOW_HOME"

pip install -r requirements.txt
pip install flake8 coverage

python -m flake8 . --exclude=.venv/ --ignore=E501,W503 --max-line-length 120
python -m coverage run -m pytest "-v"

deactivate
