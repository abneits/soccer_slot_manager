#!/bin/bash
# Install dependencies for Selenium in WSL

echo "Installing Chromium and ChromeDriver for WSL..."

# Update package list
sudo apt-get update

# Install Chromium browser and ChromeDriver
sudo apt-get install -y chromium-browser chromium-chromedriver

# Install required libraries for Chrome/Chromium
echo "Installing Chrome dependencies..."
sudo apt-get install -y \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libx11-6 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2

echo ""
echo "✓ Installation complete!"
echo ""
echo "You can now run UI tests with:"
echo "  python test_ui_selenium.py"
