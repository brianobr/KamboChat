#!/bin/bash

# Startup script for Azure App Service
# This script is used by Azure App Service to start the application

# Set the working directory
cd /home/site/wwwroot

# Install uv if not present
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Install dependencies
uv sync --frozen

# Start the application
uv run python main.py 