"""
Base agent class for the Kambo chatbot system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger
from pydantic import BaseModel


class AgentResponse(BaseModel):
    """Standard response format for all agents"""
    success: bool
    content: str
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str):
        self.name = name
        logger.info(f"Initialized agent: {name}")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process input and return response"""
        pass
    
    def log_activity(self, activity: str, details: Dict[str, Any] = None):
        """Log agent activity"""
        logger.info(f"Agent {self.name}: {activity}", extra=details or {})
    
    def handle_error(self, error: Exception, context: str = "") -> AgentResponse:
        """Handle errors and return appropriate response"""
        error_msg = f"Error in {self.name}: {str(error)}"
        if context:
            error_msg += f" | Context: {context}"
        
        logger.error(error_msg)
        return AgentResponse(
            success=False,
            content="I apologize, but I encountered an error processing your request.",
            error=error_msg
        ) 