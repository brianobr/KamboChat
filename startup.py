"""
Azure App Service startup script
"""
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the main app
from main import app

if __name__ == "__main__":
    import uvicorn
    
    # Azure App Service sets these environment variables
    port = int(os.environ.get("PORT", os.environ.get("HTTP_PLATFORM_PORT", 8000)))
    
    uvicorn.run(
        "startup:app",
        host="0.0.0.0",
        port=port,
        reload=False  # Disable reload in production
    ) 