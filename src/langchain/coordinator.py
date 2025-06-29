"""
LangChain-based coordinator for the Kambo chatbot
"""

from typing import Dict, Any, Optional
from loguru import logger
import uuid
from datetime import datetime

from .chains import KamboChain, MedicalVerifierChain, SafetyCheckChain
from src.security.input_validator import InputValidator
from src.database.connection import get_session
from src.database.models import Conversation, Message, SecurityLog


class LangChainCoordinator:
    """LangChain-based coordinator for the Kambo chatbot"""
    
    def __init__(self):
        self.kambo_chain = KamboChain()
        self.medical_verifier = MedicalVerifierChain()
        self.safety_check = SafetyCheckChain()
        self.input_validator = InputValidator()
        logger.info("LangChain coordinator initialized")
    
    async def process_message(self, user_message: str, user_id: str = None) -> Dict[str, Any]:
        """Process a user message through the LangChain pipeline"""
        
        # Generate conversation ID
        conversation_id = str(uuid.uuid4())
        
        try:
            # Step 1: Validate input
            is_valid, sanitized_message, validation_details = self.input_validator.validate_input(
                user_message, user_id
            )
            
            if not is_valid:
                self._log_security_event("input_validation_failed", user_id, validation_details)
                return {
                    "success": False,
                    "response": "I'm sorry, but I cannot process that request. Please rephrase your question.",
                    "conversation_id": conversation_id,
                    "error": "Input validation failed"
                }
            
            # Step 2: Check if question is Kambo-related
            is_kambo_related = await self.safety_check.is_kambo_related(sanitized_message)
            
            if not is_kambo_related:
                return {
                    "success": False,
                    "response": "I can only answer questions related to Kambo ceremonies and traditional Amazonian medicine. Please ask about Kambo-related topics.",
                    "conversation_id": conversation_id,
                    "metadata": {"topic_check": "failed"}
                }
            
            # Step 3: Generate Kambo response using LangChain
            kambo_result = await self.kambo_chain.process(sanitized_message, user_id)
            
            if not kambo_result["success"]:
                return {
                    "success": False,
                    "response": kambo_result["response"],
                    "conversation_id": conversation_id,
                    "error": kambo_result.get("error")
                }
            
            # Step 4: Verify medical compliance
            verification_result = await self.medical_verifier.process(
                sanitized_message, 
                kambo_result["response"], 
                user_id
            )
            
            if not verification_result["success"]:
                logger.warning("Medical verification failed, providing safe response")
                safe_response = "I apologize, but I need to provide a more appropriate response. Please consult with qualified healthcare providers for medical advice."
                
                return {
                    "success": True,
                    "response": safe_response,
                    "conversation_id": conversation_id,
                    "metadata": {
                        "medical_verification": "failed",
                        "original_response": kambo_result["response"]
                    }
                }
            
            # Step 5: Save to database
            final_response = verification_result["response"]
            self._save_conversation(conversation_id, user_id, sanitized_message, final_response)
            
            return {
                "success": True,
                "response": final_response,
                "conversation_id": conversation_id,
                "metadata": {
                    **kambo_result["metadata"],
                    **verification_result["metadata"],
                    "topic_check": "passed"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in LangChain coordinator: {e}")
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
                meta={"source": "langchain_chatbot"}
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
            
            logger.info(f"Saved conversation {conversation_id} to database")
            
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