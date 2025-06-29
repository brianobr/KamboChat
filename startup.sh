#!/bin/bash

# Startup script for Azure App Service
# This script is used by Azure App Service to start the application

# Set the working directory
cd /home/site/wwwroot

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start the application
echo "Starting Kambo Chatbot..."
python main.py 