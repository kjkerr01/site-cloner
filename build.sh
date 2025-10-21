#!/bin/bash
# Ensure pip is up-to-date
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (Chromium only)
python -m playwright install chromium --with-deps
