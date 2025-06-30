#!/bin/bash

# Startup script for Azure App Service
# This script is used by Azure App Service to start the application

# Set the working directory
cd /home/site/wwwroot

# Make sure the script is executable
chmod +x startup.sh

# Check if uv is available, if not try to install it
if ! command -v uv &> /dev/null; then
    echo "uv not found, attempting to install..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # If uv installation fails, fall back to pip
    if ! command -v uv &> /dev/null; then
        echo "uv installation failed, falling back to pip..."
        pip install -r requirements.txt
        python main.py
        exit 0
    fi
fi

# Install dependencies using uv
echo "Installing dependencies with uv..."
uv sync --frozen

# Start the application
echo "Starting application..."
uv run python main.py 