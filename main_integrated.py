"""
Integrated main application that serves both FastAPI and Gradio interfaces
Suitable for Azure App Service deployment
"""

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from loguru import logger
import uvicorn
from typing import Optional
import gradio as gr

from src.config import settings
from src.langchain.coordinator import Coordinator
from src.database.connection import init_database
from gradio_app import create_gradio_interface


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI application"""
    # Startup
    logger.info("Starting Kambo Chatbot with integrated FastAPI and Gradio...")
    init_database()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Kambo Chatbot...")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Kambo Chatbot API",
    description="A multi-agent chatbot for Kambo ceremony information with integrated Gradio interface",
    version="0.3.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize graph coordinator
chatbot = Coordinator()

# Create Gradio interface
gradio_app = create_gradio_interface()

# Mount Gradio app at /gradio
app = gr.mount_gradio_app(app, gradio_app, path="/gradio")

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"


class ChatResponse(BaseModel):
    success: bool
    response: str
    conversation_id: str
    metadata: dict = {}
    error: Optional[str] = None


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint using LangChain"""
    try:
        result = await chatbot.process_message(request.message, request.user_id)
        
        return ChatResponse(
            success=result["success"],
            response=result["response"],
            conversation_id=result["conversation_id"],
            metadata=result.get("metadata", {}),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "version": "0.3.0",
        "app_name": settings.app_name,
        "framework": "Graph Pattern",
        "interfaces": {
            "api": "/docs",
            "gradio": "/gradio"
        }
    }


@app.get("/")
async def root():
    """Root endpoint with links to both interfaces"""
    return {
        "message": "Kambo Chatbot API with Integrated Gradio Interface",
        "version": "0.3.0",
        "interfaces": {
            "api_docs": "/docs",
            "gradio_interface": "/gradio",
            "health_check": "/health"
        }
    }


if __name__ == "__main__":
    # Get port from environment variable (Azure App Service sets HTTP_PLATFORM_PORT)
    port = int(os.environ.get("PORT", os.environ.get("HTTP_PLATFORM_PORT", settings.port)))
    
    uvicorn.run(
        "main_integrated:app",
        host=settings.host,
        port=port,
        reload=settings.debug
    ) 