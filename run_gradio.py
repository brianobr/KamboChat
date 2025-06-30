#!/usr/bin/env python3
"""
Simple script to run the Gradio interface for the Kambo chatbot
"""

import os
import sys
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

def main():
    """Main function to run the Gradio interface"""
    try:
        logger.info("Starting Kambo Chatbot Gradio Interface...")
        
        # Import and run the Gradio app
        from gradio_app import create_gradio_interface, init_database
        
        # Initialize database
        init_database()
        logger.info("Database initialized successfully")
        
        # Create and launch the interface
        demo = create_gradio_interface()
        logger.info("Gradio interface created successfully")
        
        # Launch the interface
        demo.launch(
            server_name="0.0.0.0",
            server_port=8080,
            share=False,
            debug=True,
            show_error=True
        )
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting Gradio interface: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 