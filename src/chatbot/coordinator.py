"""
Main coordinator for the Kambo chatbot system
"""

from typing import Dict, Any, Optional
from loguru import logger
from src.agents.kambo_agent import KamboAgent
from src.agents.medical_verifier import MedicalVerifier
from src.security.input_validator import InputValidator
from src.database.connection import get_session
from src.database.models import Conversation, Message, MedicalVerification, SecurityLog
import uuid
from datetime import datetime


class ChatbotCoordinator:
    """Coordinates all agents and manages the chat flow"""
    
    def __init__(self):
        self.kambo_agent = KamboAgent()
        self.medical_verifier = MedicalVerifier()
        self.input_validator = InputValidator()
        logger.info("Chatbot coordinator initialized")
    
    async def process_message(self, user_message: str, user_id: str = None) -> Dict[str, Any]:
        """Process a user message through the entire pipeline"""
        
        # Generate conversation ID if not provided
        conversation_id = str(uuid.uuid4())
        
        try:
            # Step 1: Validate input
            is_valid, sanitized_message, validation_details = self.input_validator.validate_input(
                user_message, user_id
            )
            
            if not is_valid:
                # Log security event
                self._log_security_event("input_validation_failed", user_id, validation_details)
                return {
                    "success": False,
                    "response": "I'm sorry, but I cannot process that request. Please rephrase your question.",
                    "conversation_id": conversation_id,
                    "error": "Input validation failed"
                }
            
            # Step 2: Get Kambo information
            kambo_response = await self.kambo_agent.process({
                "question": sanitized_message,
                "user_id": user_id
            })
            
            if not kambo_response.success:
                return {
                    "success": False,
                    "response": kambo_response.content,
                    "conversation_id": conversation_id,
                    "metadata": kambo_response.metadata
                }
            
            # Step 3: Verify medical compliance
            verification_response = await self.medical_verifier.process({
                "response": kambo_response.content,
                "question": sanitized_message,
                "user_id": user_id
            })
            
            if not verification_response.success:
                # Regenerate response if medical issues found
                logger.warning("Medical verification failed, providing safe response")
                safe_response = "I apologize, but I need to provide a more appropriate response. Please consult with qualified healthcare providers for medical advice."
                
                return {
                    "success": True,
                    "response": safe_response,
                    "conversation_id": conversation_id,
                    "metadata": {
                        "medical_verification": "failed",
                        "original_response": kambo_response.content
                    }
                }
            
            # Step 4: Save to database
            self._save_conversation(conversation_id, user_id, sanitized_message, verification_response.content)
            
            return {
                "success": True,
                "response": verification_response.content,
                "conversation_id": conversation_id,
                "metadata": verification_response.metadata
            }
            
        except Exception as e:
            logger.error(f"Error in chatbot coordinator: {e}")
            return {
                "success": False,
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "conversation_id": conversation_id,
                "error": str(e)
            }
    
    def _save_conversation(self, conversation_id: str, user_id: str, user_message: str, assistant_response: str):
        """Save conversation to database"""
        try:
            session = get_session()
            
            # Save conversation
            conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                meta={"source": "chatbot"}
            )
            session.add(conversation)
            
            # Save user message
            user_msg = Message(
                conversation_id=conversation_id,
                role="user",
                content=user_message
            )
            session.add(user_msg)
            
            # Save assistant response
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_response
            )
            session.add(assistant_msg)
            
            session.commit()
            session.close()
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    def _log_security_event(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """Log security events"""
        try:
            session = get_session()
            
            security_log = SecurityLog(
                event_type=event_type,
                user_id=user_id,
                details=details
            )
            session.add(security_log)
            session.commit()
            session.close()
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}") 