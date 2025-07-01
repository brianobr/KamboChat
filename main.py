"""
Main application entry point for the Kambo chatbot with unified interface
"""

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from loguru import logger
import uvicorn
from typing import Optional
import gradio as gr

from src.config import settings
from src.langchain.coordinator import Coordinator
from src.database.connection import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI application"""
    # Startup
    logger.info("Starting Kambo Chatbot with LangGraph...")
    init_database()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Kambo Chatbot...")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Kambo Chatbot",
    description="A multi-agent chatbot for Kambo ceremony information using LangGraph",
    version="0.3.0",
    lifespan=lifespan
)

# Initialize LangGraph coordinator
chatbot = Coordinator()

# Remove Gradio integration and create simple HTML chat interface
@app.get("/chat")
async def chat_interface():
    """Simple HTML chat interface"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Kambo Chatbot - Chat Interface</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: #f5f5f5; 
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: white; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                overflow: hidden; 
            }
            .header { 
                background: #007bff; 
                color: white; 
                padding: 20px; 
                text-align: center; 
            }
            .chat-container { 
                height: 400px; 
                overflow-y: auto; 
                padding: 20px; 
                border-bottom: 1px solid #eee; 
            }
            .message { 
                margin: 10px 0; 
                padding: 10px; 
                border-radius: 10px; 
                max-width: 80%; 
            }
            .user-message { 
                background: #007bff; 
                color: white; 
                margin-left: auto; 
            }
            .bot-message { 
                background: #f1f1f1; 
                color: #333; 
            }
            .input-container { 
                padding: 20px; 
                display: flex; 
                gap: 10px; 
            }
            .message-input { 
                flex: 1; 
                padding: 10px; 
                border: 1px solid #ddd; 
                border-radius: 5px; 
                font-size: 16px; 
            }
            .send-button { 
                padding: 10px 20px; 
                background: #007bff; 
                color: white; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 16px; 
            }
            .send-button:hover { 
                background: #0056b3; 
            }
            .send-button:disabled { 
                background: #ccc; 
                cursor: not-allowed; 
            }
            .loading { 
                text-align: center; 
                color: #666; 
                font-style: italic; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🐸 Kambo Chatbot</h1>
                <p>Ask me anything about Kambo ceremonies, traditional medicine, and healing practices.</p>
            </div>
            
            <div class="chat-container" id="chatContainer">
                <div class="message bot-message">
                    Hello! I'm here to help you learn about Kambo ceremonies and traditional Amazonian medicine. What would you like to know?
                </div>
            </div>
            
            <div class="input-container">
                <input type="text" id="messageInput" class="message-input" placeholder="Type your message here..." />
                <button id="sendButton" class="send-button">Send</button>
            </div>
        </div>

        <script>
            const chatContainer = document.getElementById("chatContainer");
            const messageInput = document.getElementById("messageInput");
            const sendButton = document.getElementById("sendButton");
            let userId = "web_user_" + Math.random().toString(36).substr(2, 9);

            function addMessage(content, isUser = false) {
                const messageDiv = document.createElement("div");
                messageDiv.className = `message ${isUser ? "user-message" : "bot-message"}`;
                messageDiv.textContent = content;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            function addLoadingMessage() {
                const loadingDiv = document.createElement("div");
                loadingDiv.className = "message bot-message loading";
                loadingDiv.id = "loadingMessage";
                loadingDiv.textContent = "Thinking...";
                chatContainer.appendChild(loadingDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            function removeLoadingMessage() {
                const loadingMessage = document.getElementById("loadingMessage");
                if (loadingMessage) {
                    loadingMessage.remove();
                }
            }

            async function sendMessage() {
                const message = messageInput.value.trim();
                if (!message) return;

                console.log("Sending message:", message);

                // Disable input and button
                messageInput.disabled = true;
                sendButton.disabled = true;

                // Add user message
                addMessage(message, true);
                messageInput.value = "";

                // Add loading message
                addLoadingMessage();

                try {
                    const response = await fetch("/api/chat", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            message: message,
                            user_id: userId
                        })
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    
                    console.log("Received response:", data);
                    
                    // Remove loading message
                    removeLoadingMessage();

                    if (data.success) {
                        addMessage(data.response);
                    } else {
                        addMessage("I am sorry, I can't answer that question: " + (data.error || "Unknown error"));
                    }
                } catch (error) {
                    console.error("Error sending message:", error);
                    removeLoadingMessage();
                    addMessage("Sorry, there was an error processing your request: " + error.message);
                } finally {
                    // Re-enable input and button
                    messageInput.disabled = false;
                    sendButton.disabled = false;
                    messageInput.focus();
                }
            }

            // Event listeners
            sendButton.addEventListener("click", sendMessage);
            messageInput.addEventListener("keypress", function(e) {
                if (e.key === "Enter") {
                    sendMessage();
                }
            });

            // Focus on input when page loads
            messageInput.focus();
        </script>
    </body>
    </html>
    """)

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


@app.post("/api/chat", response_model=ChatResponse)
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


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "version": "0.3.0",
        "app_name": settings.app_name,
        "framework": "LangGraph"
    }


@app.get("/api/conversation-history/{user_id}")
async def get_conversation_history(user_id: str, limit: int = 10):
    """Get conversation history for a user"""
    try:
        history = chatbot._load_conversation_history(user_id, limit)
        return {
            "user_id": user_id,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving conversation history")


@app.get("/")
async def root():
    """Root endpoint with navigation"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Kambo Chatbot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .nav { background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }
            .nav a { display: inline-block; margin: 10px; padding: 10px 20px; 
                     background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            .nav a:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🐸 Kambo Chatbot</h1>
            <p>Welcome to the Kambo information assistant! Choose your interface:</p>
            
            <div class="nav">
                <a href="/chat">💬 Chat Interface</a>
                <a href="/docs">📚 API Documentation</a>
                <a href="/api/health">🏥 Health Check</a>
            </div>
            
            <h2>Features:</h2>
            <ul>
                <li><strong>Chat Interface:</strong> Interactive web chat with streaming responses</li>
                <li><strong>API Access:</strong> Programmatic access for integrations</li>
                <li><strong>Conversation Memory:</strong> Remembers your name and previous topics</li>
                <li><strong>Medical Safety:</strong> Verified responses with no medical advice</li>
            </ul>
            
            <h2>Quick Start:</h2>
            <p>Click "Chat Interface" to start a conversation, or use the API endpoints for programmatic access.</p>
        </div>
    </body>
    </html>
    """)


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    port = settings.port
    if "--port" in sys.argv:
        try:
            port_index = sys.argv.index("--port")
            if port_index + 1 < len(sys.argv):
                port = int(sys.argv[port_index + 1])
        except (ValueError, IndexError):
            pass
    
    # Get port from environment variable (Azure App Service sets HTTP_PLATFORM_PORT)
    port = int(os.environ.get("PORT", os.environ.get("HTTP_PLATFORM_PORT", port)))
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=port,
        reload=settings.debug
    ) 