#!/usr/bin/env bash
set -eux

pip install --upgrade pip
pip install -r requirements.txt

# Force playwright to install browsers into the project folder
mkdir -p .playwright
PLAYWRIGHT_BROWSERS_PATH=.playwright python -m playwright install chromium
