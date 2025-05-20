#!/bin/bash
set -e

apt-get update
apt-get install -y chromium-browser chromium-driver mpg123

apt-get clean
rm -rf /var/lib/apt/lists/*
