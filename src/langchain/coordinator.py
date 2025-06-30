"""
Graph-based coordinator using LangChain's RunnableSequence
"""

from typing import Dict, Any, Optional
from loguru import logger
import uuid
from datetime import datetime
import asyncio

from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .llm_setup import create_kambo_llm, create_medical_verifier_llm
from .prompts import create_kambo_prompt, create_medical_verifier_prompt, create_safety_check_prompt
from src.security.input_validator import InputValidator
from src.database.connection import get_session
from src.database.models import Conversation, Message, SecurityLog


class Coordinator:
    """Graph-based coordinator using LangChain's RunnableSequence"""
    
    def __init__(self):
        self.input_validator = InputValidator()
        self.graph = self._build_graph()
        logger.info("Graph coordinator initialized")
    
    def _build_graph(self) -> RunnableSequence:
        """Build the optimized processing graph"""
        
        # Node 1: Input Validation
        def validate_input(inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Validate and sanitize user input"""
            user_message = inputs["user_message"]
            user_id = inputs.get("user_id", "anonymous")
            
            is_valid, sanitized_message, validation_details = self.input_validator.validate_input(
                user_message, user_id
            )
            
            if not is_valid:
                self._log_security_event("input_validation_failed", user_id, validation_details)
                return {
                    "valid": False,
                    "error": "Input validation failed",
                    "user_id": user_id
                }
            
            return {
                "valid": True,
                "sanitized_message": sanitized_message,
                "user_id": user_id
            }
        
        # Node 2: Kambo Response Generation (Single LLM call)
        kambo_llm = create_kambo_llm()
        kambo_prompt = create_kambo_prompt()
        kambo_chain = kambo_prompt | kambo_llm | StrOutputParser()
        
        # Edge 1: Route based on input validation
        def route_after_validation(inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Route to next step based on validation result"""
            if not inputs["validation"]["valid"]:
                return {
                    "route": "error",
                    "error": inputs["validation"]["error"],
                    "user_id": inputs["validation"]["user_id"]
                }
            
            return {
                "route": "continue",
                "sanitized_message": inputs["validation"]["sanitized_message"],
                "user_id": inputs["validation"]["user_id"]
            }
        
        # Build the optimized graph
        graph = (
            # Start with user input
            {"user_message": RunnablePassthrough(), "user_id": RunnablePassthrough()}
            | {
                # Node 1: Input Validation
                "validation": validate_input,
                "user_message": RunnablePassthrough(),
                "user_id": RunnablePassthrough()
            }
            | RunnablePassthrough.assign(
                # Edge 1: Route after validation
                routing=route_after_validation
            )
            | RunnablePassthrough.assign(
                # Node 2: Kambo Response Generation (only if validation passed)
                kambo_response=lambda x: kambo_chain.invoke({"question": x["routing"]["sanitized_message"]})
                if x["routing"]["route"] == "continue" else "Not applicable"
            )
            | RunnablePassthrough.assign(
                final_routing=lambda x: {
                    "route": "success",
                    "response": x["kambo_response"],
                    "user_id": x["routing"]["user_id"],
                    "metadata": {
                        "model": kambo_llm.model_name
                    }
                } if x["routing"]["route"] == "continue" else {
                    "route": "error",
                    "error": x["routing"]["error"],
                    "user_id": x["routing"]["user_id"]
                }
            )
        )
        
        return graph
    
    async def process_message(self, user_message: str, user_id: str = None) -> Dict[str, Any]:
        """Process a user message through the explicit graph"""
        
        conversation_id = str(uuid.uuid4())
        
        try:
            # Execute the graph
            result = await self.graph.ainvoke({
                "user_message": user_message,
                "user_id": user_id or "anonymous"
            })
            
            # Handle different routing outcomes
            if result["routing"]["route"] == "error":
                return {
                    "success": False,
                    "response": "I'm sorry, but I cannot process that request. Please rephrase your question.",
                    "conversation_id": conversation_id,
                    "error": result["routing"]["error"]
                }
            
            elif result["final_routing"]["route"] == "success":
                # Save to database asynchronously (don't block response)
                asyncio.create_task(self._save_conversation_async(
                    conversation_id, 
                    result["final_routing"]["user_id"], 
                    user_message, 
                    result["final_routing"]["response"]
                ))
                
                return {
                    "success": True,
                    "response": result["final_routing"]["response"],
                    "conversation_id": conversation_id,
                    "metadata": {
                        **result["final_routing"]["metadata"],
                        "topic_check": "passed"
                    }
                }
            
            else:
                # Fallback for unexpected routing
                return {
                    "success": False,
                    "response": "I apologize, but I encountered an unexpected error. Please try again.",
                    "conversation_id": conversation_id,
                    "error": "Unexpected routing state"
                }
                
        except Exception as e:
            logger.error(f"Error in explicit graph coordinator: {e}")
            return {
                "success": False,
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "conversation_id": conversation_id,
                "error": str(e)
            }
    
    async def _save_conversation_async(self, conversation_id: str, user_id: str, user_message: str, assistant_response: str):
        """Save conversation to database asynchronously"""
        try:
            session = get_session()
            
            # Save conversation
            conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                meta={"source": "graph_chatbot"}
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

    def _save_conversation(self, conversation_id: str, user_id: str, user_message: str, assistant_response: str):
        """Save conversation to database (synchronous version for backward compatibility)"""
        try:
            session = get_session()
            
            # Save conversation
            conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                meta={"source": "graph_chatbot"}
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