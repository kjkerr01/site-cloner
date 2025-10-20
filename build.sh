#!/bin/bash
# Upgrade pip
pip install --upgrade pip
# Install Playwright browsers (only Chromium)
python -m playwright install chromium
