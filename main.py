"""
Main application entry point for the Kambo chatbot
"""

import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loguru import logger
import uvicorn
from typing import Optional

from src.config import settings
from src.chatbot.coordinator import ChatbotCoordinator
from src.database.connection import init_database


# Initialize FastAPI app
app = FastAPI(
    title="Kambo Chatbot API",
    description="A multi-agent chatbot for Kambo ceremony information",
    version="0.1.0"
)

# Initialize components
chatbot = ChatbotCoordinator()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Kambo Chatbot...")
    init_database()
    logger.info("Database initialized successfully")


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
    """Main chat endpoint"""
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
        "version": "0.1.0",
        "app_name": settings.app_name
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Kambo Chatbot API",
        "version": "0.1.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 