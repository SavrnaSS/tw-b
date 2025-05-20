 #!/bin/bash
set -e

# Install Chromium and Chromium Driver
apt-get update
apt-get install -y chromium chromium-driver

# Clean up cache to reduce build size
apt-get clean
rm -rf /var/lib/apt/lists/*
