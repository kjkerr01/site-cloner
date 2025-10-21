#!/usr/bin/env bash
set -eux

export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/src/.playwright

pip install --upgrade pip
pip install -r requirements.txt

python -m playwright install chromium
