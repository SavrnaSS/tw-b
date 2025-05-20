#!/bin/bash
set -e

# Update package lists
apt-get update

# Install headless Chromium, ChromeDriver, and mpg123 for gTTS notifications
apt-get install -y chromium-browser chromium-driver mpg123

# Clean up apt cache to reduce image size
apt-get clean
rm -rf /var/lib/apt/lists/*
