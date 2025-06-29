"""
Explicit graph-based coordinator using LangChain's RunnableSequence
"""

from typing import Dict, Any, Optional
from loguru import logger
import uuid
from datetime import datetime

from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .llm_setup import create_kambo_llm, create_medical_verifier_llm
from .prompts import create_kambo_prompt, create_medical_verifier_prompt, create_safety_check_prompt
from src.security.input_validator import InputValidator
from src.database.connection import get_session
from src.database.models import Conversation, Message, SecurityLog


class ExplicitGraphCoordinator:
    """Explicit graph-based coordinator using LangChain's RunnableSequence"""
    
    def __init__(self):
        self.input_validator = InputValidator()
        self.graph = self._build_graph()
        logger.info("Explicit graph coordinator initialized")
    
    def _build_graph(self) -> RunnableSequence:
        """Build the explicit processing graph"""
        
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
        
        # Node 2: Safety Check (Kambo-related classification)
        safety_llm = create_medical_verifier_llm()  # Deterministic for classification
        safety_prompt = create_safety_check_prompt()
        safety_chain = safety_prompt | safety_llm | StrOutputParser()
        
        def parse_safety_result(inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Parse the safety check result"""
            safety_result = inputs["safety_check"].strip().upper()
            is_kambo_related = "YES" in safety_result
            
            logger.info(f"Safety check: question is {'Kambo-related' if is_kambo_related else 'not Kambo-related'}")
            
            return {
                **inputs,
                "is_kambo_related": is_kambo_related
            }
        
        # Node 3: Kambo Response Generation
        kambo_llm = create_kambo_llm()
        kambo_prompt = create_kambo_prompt()
        kambo_chain = kambo_prompt | kambo_llm | StrOutputParser()
        
        # Node 4: Medical Verification
        medical_llm = create_medical_verifier_llm()
        medical_prompt = create_medical_verifier_prompt()
        medical_chain = medical_prompt | medical_llm | StrOutputParser()
        
        def parse_verification_result(inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Parse medical verification result"""
            verified_response = inputs["medical_verification"].strip()
            original_response = inputs["kambo_response"]
            
            # Check if response was modified (indicating issues)
            is_safe = verified_response == original_response
            
            logger.info(f"Medical verification {'passed' if is_safe else 'failed'}")
            
            return {
                **inputs,
                "is_safe": is_safe,
                "final_response": verified_response
            }
        
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
        
        # Edge 2: Route based on safety check
        def route_after_safety(inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Route based on whether question is Kambo-related"""
            if not inputs["safety_result"]["is_kambo_related"]:
                return {
                    "route": "reject",
                    "message": "I can only answer questions related to Kambo ceremonies and traditional Amazonian medicine. Please ask about Kambo-related topics.",
                    "user_id": inputs["safety_result"]["user_id"]
                }
            
            return {
                "route": "kambo",
                "question": inputs["safety_result"]["sanitized_message"],
                "user_id": inputs["safety_result"]["user_id"]
            }
        
        # Edge 3: Route based on medical verification
        def route_after_verification(inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Route based on medical verification result"""
            if not inputs["verification_result"]["is_safe"]:
                logger.warning("Medical verification failed, providing safe response")
                return {
                    "route": "safe_fallback",
                    "response": "I apologize, but I need to provide a more appropriate response. Please consult with qualified healthcare providers for medical advice.",
                    "user_id": inputs["verification_result"]["user_id"],
                    "metadata": {
                        "medical_verification": "failed",
                        "original_response": inputs["verification_result"]["kambo_response"]
                    }
                }
            
            return {
                "route": "success",
                "response": inputs["verification_result"]["final_response"],
                "user_id": inputs["verification_result"]["user_id"],
                "metadata": {
                    "medical_verification": "passed",
                    "model": kambo_llm.model_name
                }
            }
        
        # Build the explicit graph
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
                # Node 2: Safety Check (only if validation passed)
                safety_check=lambda x: safety_chain.invoke({"question": x["routing"]["sanitized_message"]})
                if x["routing"]["route"] == "continue" else "NO"
            )
            | RunnablePassthrough.assign(
                # Parse safety result
                safety_result=lambda x: parse_safety_result({
                    "safety_check": x["safety_check"],
                    "sanitized_message": x["routing"]["sanitized_message"],
                    "user_id": x["routing"]["user_id"]
                }) if x["routing"]["route"] == "continue" else {"is_kambo_related": False}
            )
            | RunnablePassthrough.assign(
                # Edge 2: Route after safety check
                safety_routing=route_after_safety
            )
            | RunnablePassthrough.assign(
                # Node 3: Kambo Response Generation (only if Kambo-related)
                kambo_response=lambda x: kambo_chain.invoke({"question": x["safety_routing"]["question"]})
                if x["safety_routing"]["route"] == "kambo" else "Not applicable"
            )
            | RunnablePassthrough.assign(
                # Node 4: Medical Verification (only if Kambo response generated)
                medical_verification=lambda x: medical_chain.invoke({
                    "question": x["safety_routing"]["question"],
                    "response": x["kambo_response"]
                }) if x["safety_routing"]["route"] == "kambo" else "Not applicable"
            )
            | RunnablePassthrough.assign(
                # Parse verification result
                verification_result=lambda x: parse_verification_result({
                    "medical_verification": x["medical_verification"],
                    "kambo_response": x["kambo_response"],
                    "user_id": x["safety_routing"]["user_id"]
                }) if x["safety_routing"]["route"] == "kambo" else {
                    "is_safe": True,
                    "final_response": "Not applicable",
                    "user_id": x["safety_routing"]["user_id"]
                }
            )
            | RunnablePassthrough.assign(
                # Edge 3: Route after verification
                final_routing=route_after_verification
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
            
            elif result["safety_routing"]["route"] == "reject":
                return {
                    "success": False,
                    "response": result["safety_routing"]["message"],
                    "conversation_id": conversation_id,
                    "metadata": {"topic_check": "failed"}
                }
            
            elif result["final_routing"]["route"] == "safe_fallback":
                return {
                    "success": True,
                    "response": result["final_routing"]["response"],
                    "conversation_id": conversation_id,
                    "metadata": result["final_routing"]["metadata"]
                }
            
            elif result["final_routing"]["route"] == "success":
                # Save to database
                self._save_conversation(
                    conversation_id, 
                    result["final_routing"]["user_id"], 
                    user_message, 
                    result["final_routing"]["response"]
                )
                
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
    
    def _save_conversation(self, conversation_id: str, user_id: str, user_message: str, assistant_response: str):
        """Save conversation to database"""
        try:
            session = get_session()
            
            # Save conversation
            conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                meta={"source": "explicit_graph_chatbot"}
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