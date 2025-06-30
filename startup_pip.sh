#!/bin/bash

# Startup script for Azure App Service using pip
# This script is used by Azure App Service to start the application

# Set the working directory
cd /home/site/wwwroot

# Make sure the script is executable
chmod +x startup_pip.sh

# Install dependencies using pip
echo "Installing dependencies with pip..."
pip install -r requirements.txt

# Start the application
echo "Starting application..."
python main.py 