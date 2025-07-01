"""
LangGraph-based coordinator for the Kambo chatbot with medical verification feedback loop
"""

from typing import Dict, Any, Optional, TypedDict, Annotated, List
from loguru import logger
import uuid
import asyncio

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .llm_setup import create_kambo_llm, create_medical_verifier_llm
from .prompts import create_kambo_prompt, create_safety_check_prompt, create_medical_verifier_prompt
from src.security.input_validator import InputValidator
from src.database.connection import get_session
from src.database.models import Conversation, Message, SecurityLog


class ChatState(TypedDict):
    """State for the LangGraph chat flow with medical verification feedback loop and memory"""
    messages: Annotated[list, add_messages]
    user_message: str
    user_id: str
    conversation_id: str
    conversation_history: List[Dict[str, str]]  # New: conversation history
    validation_result: Optional[Dict[str, Any]]
    moderation_result: Optional[Dict[str, Any]]
    safety_check_result: Optional[bool]
    rag_context: Optional[str]
    kambo_response: Optional[str]
    medical_verification_result: Optional[Dict[str, Any]]
    medical_verification_attempts: int
    medical_verification_feedback: List[str]
    final_response: Optional[str]
    error: Optional[str]
    metadata: Optional[Dict[str, Any]]


class Coordinator:
    """LangGraph-based coordinator with medical verification feedback loop and conversation memory"""
    
    def __init__(self):
        self.input_validator = InputValidator()
        self.graph = self._build_graph()
        logger.info("LangGraph coordinator with memory initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph processing flow"""
        
        # Create the state graph
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("validate_input", self._validate_input_node)
        workflow.add_node("moderate_input", self._moderate_input_node)
        workflow.add_node("check_safety", self._check_safety_node)
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("generate_kambo_response", self._generate_kambo_response_node)
        workflow.add_node("verify_medical", self._verify_medical_node)
        workflow.add_node("check_retry_limit", self._check_retry_limit_node)
        workflow.add_node("enhanced_kambo_response", self._enhanced_kambo_response_node)
        workflow.add_node("create_final_response", self._create_final_response_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Set entry point
        workflow.set_entry_point("validate_input")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "validate_input",
            self._should_continue_after_validation,
            {
                "continue": "moderate_input",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "moderate_input",
            self._should_continue_after_moderation,
            {
                "continue": "check_safety",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "check_safety",
            self._should_generate_response,
            {
                "continue": "retrieve_context",
                "reject": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "retrieve_context",
            self._should_generate_response,
            {
                "continue": "generate_kambo_response",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_kambo_response",
            self._should_verify_medical,
            {
                "continue": "verify_medical",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "verify_medical",
            self._should_retry_or_continue,
            {
                "safe": "create_final_response",
                "retry": "check_retry_limit",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "check_retry_limit",
            self._should_retry_or_fail,
            {
                "retry": "enhanced_kambo_response",
                "fail": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "enhanced_kambo_response",
            self._should_verify_medical,
            {
                "continue": "verify_medical",
                "error": "handle_error"
            }
        )
        
        # Add final edges to END
        workflow.add_edge("create_final_response", END)
        workflow.add_edge("handle_error", END)
        
        # Compile the graph
        return workflow.compile()
    
    def _validate_input_node(self, state: ChatState) -> ChatState:
        """Validate and sanitize user input"""
        user_message = state["user_message"]
        user_id = state["user_id"]
        
        logger.info(f"Validating input for user {user_id}")
        
        is_valid, sanitized_message, validation_details = self.input_validator.validate_input(
            user_message, user_id
        )
        
        if not is_valid:
            self._log_security_event("input_validation_failed", user_id, validation_details)
            return {
                **state,
                "validation_result": {
                    "valid": False,
                    "error": "Input validation failed",
                    "details": validation_details
                }
            }
        
        return {
            **state,
            "validation_result": {
                "valid": True,
                "sanitized_message": sanitized_message
            }
        }
    
    def _moderate_input_node(self, state: ChatState) -> ChatState:
        """Moderate input for policy violations"""
        if not state["validation_result"]["valid"]:
            return state
        
        sanitized_message = state["validation_result"]["sanitized_message"]
        user_id = state["user_id"]
        
        logger.info(f"Moderating input for user {user_id}")
        
        try:
            # Simple moderation check - can be enhanced with external APIs
            # For now, check for obvious policy violations
            violations = []
            
            # Check for hate speech indicators
            hate_indicators = ["hate", "kill", "harm", "attack"]
            if any(indicator in sanitized_message.lower() for indicator in hate_indicators):
                violations.append("Potential hate speech detected")
            
            # Check for self-harm indicators
            self_harm_indicators = ["kill myself", "end my life", "suicide"]
            if any(indicator in sanitized_message.lower() for indicator in self_harm_indicators):
                violations.append("Self-harm content detected")
            
            if violations:
                return {
                    **state,
                    "moderation_result": {
                        "passed": False,
                        "violations": violations
                    }
                }
            
            return {
                **state,
                "moderation_result": {
                    "passed": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error in moderation: {e}")
            return {
                **state,
                "moderation_result": {
                    "passed": False,
                    "violations": [f"Moderation error: {str(e)}"]
                }
            }
    
    def _check_safety_node(self, state: ChatState) -> ChatState:
        """Check if the question is Kambo-related"""
        if not state["moderation_result"]["passed"]:
            return state
        
        sanitized_message = state["validation_result"]["sanitized_message"]
        user_id = state["user_id"]
        
        logger.info(f"Checking safety for user {user_id}")
        
        try:
            # Create safety check chain
            llm = create_kambo_llm()
            prompt = create_safety_check_prompt()
            chain = prompt | llm | StrOutputParser()
            
            result = chain.invoke({"question": sanitized_message})
            response = result.strip().upper()
            
            is_kambo_related = "YES" in response
            
            logger.info(f"Safety check result: {'Kambo-related' if is_kambo_related else 'Not Kambo-related'}")
            
            if is_kambo_related:
                return {
                    **state,
                    "safety_check_result": True
                }
            else:
                return {
                    **state,
                    "safety_check_result": False,
                    "error": "safety_check_failed: Question is not Kambo-related"
                }
            
        except Exception as e:
            logger.error(f"Error in safety check: {e}")
            return {
                **state,
                "safety_check_result": False,
                "error": f"Safety check failed: {str(e)}"
            }
    
    def _retrieve_context_node(self, state: ChatState) -> ChatState:
        """Retrieve relevant context from knowledge base (RAG)"""
        if not state["safety_check_result"]:
            return state
        
        sanitized_message = state["validation_result"]["sanitized_message"]
        user_id = state["user_id"]
        
        logger.info(f"Retrieving context for user {user_id}")
        
        try:
            # For now, return a placeholder context
            # This can be enhanced with actual RAG implementation
            context = "Kambo is a traditional Amazonian medicine used in healing ceremonies."
            
            return {
                **state,
                "rag_context": context
            }
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return {
                **state,
                "rag_context": "",
                "error": f"Context retrieval failed: {str(e)}"
            }
    
    def _generate_kambo_response_node(self, state: ChatState) -> ChatState:
        """Generate Kambo response using LLM"""
        if not state["safety_check_result"]:
            return state
        
        sanitized_message = state["validation_result"]["sanitized_message"]
        rag_context = state.get("rag_context", "")
        user_id = state["user_id"]
        
        logger.info(f"Generating Kambo response for user {user_id}")
        
        try:
            # Create Kambo response chain
            llm = create_kambo_llm()
            prompt = create_kambo_prompt()
            chain = prompt | llm | StrOutputParser()
            
            # Include RAG context if available
            prompt_input = {"question": sanitized_message}
            if rag_context:
                prompt_input["context"] = rag_context
            
            result = chain.invoke(prompt_input)
            response = result.strip()
            
            logger.info(f"Generated response for user {user_id} (length: {len(response)})")
            
            return {
                **state,
                "kambo_response": response,
                "metadata": {
                    "model": llm.model_name,
                    "response_length": len(response),
                    "attempt": state.get("medical_verification_attempts", 0) + 1
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating Kambo response: {e}")
            return {
                **state,
                "error": f"Response generation failed: {str(e)}"
            }
    
    def _verify_medical_node(self, state: ChatState) -> ChatState:
        """Verify that the response doesn't contain medical advice"""
        kambo_response = state.get("kambo_response", "")
        user_id = state["user_id"]
        
        logger.info(f"Verifying medical content for user {user_id}")
        
        try:
            # Create medical verification chain
            llm = create_medical_verifier_llm()
            prompt = create_medical_verifier_prompt()
            chain = prompt | llm | StrOutputParser()
            
            result = chain.invoke({
                "question": state["user_message"],
                "response": kambo_response
            })
            
            # Parse the verification result
            response_text = result.strip().upper()
            is_safe = "SAFE" in response_text
            is_medical_advice = "MEDICAL_ADVICE" in response_text
            
            # Extract detailed feedback
            feedback = ""
            if not is_safe:
                # Extract the specific issues mentioned
                if "DIAGNOSIS" in response_text:
                    feedback += "Contains diagnostic information. "
                if "TREATMENT" in response_text:
                    feedback += "Contains treatment recommendations. "
                if "DOSAGE" in response_text:
                    feedback += "Contains dosage information. "
                if "CURE" in response_text:
                    feedback += "Contains curative claims. "
                if "HEAL" in response_text:
                    feedback += "Contains healing promises. "
                
                if not feedback:
                    feedback = "Contains medical advice that should be avoided."
            
            logger.info(f"Medical verification result: {'Safe' if is_safe else 'Unsafe'} - {feedback}")
            
            return {
                **state,
                "medical_verification_result": {
                    "is_safe": is_safe,
                    "is_medical_advice": is_medical_advice,
                    "feedback": feedback,
                    "raw_response": result.strip()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in medical verification: {e}")
            return {
                **state,
                "medical_verification_result": {
                    "is_safe": False,
                    "is_medical_advice": True,
                    "feedback": f"Verification failed: {str(e)}",
                    "raw_response": ""
                }
            }
    
    def _check_retry_limit_node(self, state: ChatState) -> ChatState:
        """Check if we should retry or fail based on attempt count"""
        attempts = state.get("medical_verification_attempts", 0)
        max_attempts = 3
        
        logger.info(f"Checking retry limit: attempt {attempts + 1}/{max_attempts}")
        
        if attempts < max_attempts:
            return {
                **state,
                "medical_verification_attempts": attempts + 1
            }
        else:
            return {
                **state,
                "error": f"Maximum retry attempts ({max_attempts}) exceeded for medical verification"
            }
    
    def _enhanced_kambo_response_node(self, state: ChatState) -> ChatState:
        """Generate enhanced Kambo response with medical verification feedback"""
        sanitized_message = state["validation_result"]["sanitized_message"]
        rag_context = state.get("rag_context", "")
        medical_feedback = state["medical_verification_result"]["feedback"]
        attempts = state.get("medical_verification_attempts", 0)
        user_id = state["user_id"]
        
        logger.info(f"Generating enhanced Kambo response for user {user_id} (attempt {attempts})")
        
        try:
            # Create enhanced prompt with medical verification feedback
            enhanced_prompt = ChatPromptTemplate.from_template("""
            You are a knowledgeable guide about Kambo ceremonies and traditional practices.
            
            IMPORTANT: Your previous response was flagged for containing medical advice. 
            Please avoid the following issues: {medical_feedback}
            
            Focus on providing educational information about Kambo ceremonies, cultural context, 
            and traditional practices without making medical claims or giving health advice.
            
            User Question: {question}
            
            Context: {context}
            
            Please provide a response that is informative but avoids medical advice.
            """)
            
            llm = create_kambo_llm()
            chain = enhanced_prompt | llm | StrOutputParser()
            
            # Include RAG context if available
            prompt_input = {
                "question": sanitized_message,
                "medical_feedback": medical_feedback,
                "context": rag_context or "Kambo is a traditional Amazonian medicine used in healing ceremonies."
            }
            
            result = chain.invoke(prompt_input)
            response = result.strip()
            
            logger.info(f"Generated enhanced response for user {user_id} (length: {len(response)})")
            
            return {
                **state,
                "kambo_response": response,
                "medical_verification_feedback": state.get("medical_verification_feedback", []) + [medical_feedback],
                "metadata": {
                    "model": llm.model_name,
                    "response_length": len(response),
                    "attempt": attempts,
                    "enhanced": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating enhanced Kambo response: {e}")
            return {
                **state,
                "error": f"Enhanced response generation failed: {str(e)}"
            }
    
    def _create_final_response_node(self, state: ChatState) -> ChatState:
        """Create the final response"""
        if state.get("error"):
            return state
        
        kambo_response = state.get("kambo_response", "")
        user_id = state["user_id"]
        attempts = state.get("medical_verification_attempts", 0)
        
        logger.info(f"Creating final response for user {user_id}")
        
        # Add medical disclaimer
        medical_disclaimer = (
            "\n\n⚠️ **Medical Disclaimer**: This information is for educational purposes only. "
            "Kambo ceremonies should only be performed by trained practitioners. "
            "Always consult with qualified healthcare providers before participating in any traditional healing practices."
        )
        
        # Add retry information if applicable
        retry_info = ""
        if attempts > 1:
            retry_info = f"\n\n*This response was refined after {attempts} verification attempts to ensure it meets safety guidelines.*"
        
        final_response = kambo_response + medical_disclaimer + retry_info
        
        return {
            **state,
            "final_response": final_response
        }
    
    def _handle_error_node(self, state: ChatState) -> ChatState:
        """Handle errors and create error responses"""
        error_message = state.get("error")
        user_id = state["user_id"]
        
        logger.warning(f"Handling error for user {user_id}: {error_message}")
        
        # Ensure error_message is a string
        if not error_message:
            error_message = "An unexpected error occurred"
        
        # Create appropriate error response based on the error type
        if error_message and "safety_check_failed" in error_message:
            final_response = "I can only provide information about Kambo ceremonies and traditional practices. Please ask a Kambo-related question."
        elif "validation" in error_message.lower():
            final_response = "I'm sorry, but I cannot process that request. Please rephrase your question."
        elif "moderation" in error_message.lower():
            final_response = "I'm sorry, but your message violates our content policy. Please rephrase your question."
        elif "safety" in error_message.lower():
            final_response = "I can only provide information about Kambo ceremonies and traditional practices. Please ask a Kambo-related question."
        elif "medical verification" in error_message.lower():
            final_response = "I apologize, but I'm unable to provide a safe response to your question. Please consult with qualified healthcare providers for medical advice."
        elif "retry attempts" in error_message.lower():
            final_response = "I apologize, but I'm unable to provide a response that meets our safety guidelines. Please consult with qualified healthcare providers for medical advice."
        else:
            final_response = "I apologize, but I encountered an error processing your request. Please try again."
        
        return {
            **state,
            "final_response": final_response,
            "error": error_message
        }
    
    def _should_continue_after_validation(self, state: ChatState) -> str:
        """Determine if we should continue after validation"""
        if state["validation_result"]["valid"]:
            return "continue"
        return "error"
    
    def _should_continue_after_moderation(self, state: ChatState) -> str:
        """Determine if we should continue after moderation"""
        if state["moderation_result"]["passed"]:
            return "continue"
        return "error"
    
    def _should_generate_response(self, state: ChatState) -> str:
        """Determine if we should generate a response"""
        if state["safety_check_result"]:
            return "continue"
        return "reject"
    
    def _should_verify_medical(self, state: ChatState) -> str:
        """Determine if we should verify medical content"""
        if state.get("kambo_response"):
            return "continue"
        return "error"
    
    def _should_retry_or_continue(self, state: ChatState) -> str:
        """Determine if we should retry or continue based on medical verification"""
        verification_result = state["medical_verification_result"]
        
        if verification_result["is_safe"]:
            return "safe"
        elif verification_result["is_medical_advice"]:
            return "retry"
        else:
            return "error"
    
    def _should_retry_or_fail(self, state: ChatState) -> str:
        """Determine if we should retry or fail based on attempt count"""
        attempts = state.get("medical_verification_attempts", 0)
        max_attempts = 3
        
        if attempts < max_attempts:
            return "retry"
        else:
            return "fail"
    
    async def process_message(self, user_message: str, user_id: str = None) -> Dict[str, Any]:
        """Process a user message through the LangGraph with memory"""
        
        conversation_id = str(uuid.uuid4())
        user_id = user_id or "anonymous"
        
        try:
            # Load conversation history
            conversation_history = self._load_conversation_history(user_id)
            
            # Initialize state with memory
            initial_state = {
                "messages": [HumanMessage(content=user_message)],
                "user_message": user_message,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "conversation_history": conversation_history,  # Include history
                "validation_result": None,
                "moderation_result": None,
                "safety_check_result": None,
                "rag_context": None,
                "kambo_response": None,
                "medical_verification_result": None,
                "medical_verification_attempts": 0,
                "medical_verification_feedback": [],
                "final_response": None,
                "error": None,
                "metadata": {}
            }
            
            # Execute the graph
            result = await self.graph.ainvoke(initial_state)
            
            # Ensure result is always a dict
            if isinstance(result, dict):
                final_state = result
            else:
                final_state = {"final_response": str(result), "error": "Unexpected result type"}
            
            # Determine success
            success = final_state.get("final_response") is not None and not final_state.get("error")
            
            # Save to database asynchronously if successful
            if success:
                asyncio.create_task(self._save_conversation_async(
                    conversation_id,
                    user_id,
                    user_message,
                    final_state["final_response"]
                ))
            
            return {
                "success": success,
                "response": final_state.get("final_response", "I apologize, but I encountered an error."),
                "conversation_id": conversation_id,
                "metadata": final_state.get("metadata", {}),
                "error": final_state.get("error")
            }
            
        except Exception as e:
            logger.error(f"Error in LangGraph coordinator: {e}")
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
                meta={"source": "langgraph_chatbot"}
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
    
    def get_graph_info(self) -> Dict[str, Any]:
        """Get information about the LangGraph structure"""
        return {
            "graph_type": "LangGraph StateGraph",
            "nodes": [
                "validate_input",
                "moderate_input",
                "check_safety",
                "retrieve_context",
                "generate_kambo_response",
                "verify_medical",
                "check_retry_limit",
                "enhanced_kambo_response",
                "create_final_response",
                "handle_error"
            ],
            "edges": [
                "START -> validate_input",
                "validate_input -> (continue/error)",
                "moderate_input -> (continue/error)",
                "check_safety -> (continue/reject)",
                "retrieve_context -> (continue/error)",
                "generate_kambo_response -> (continue/error)",
                "verify_medical -> (safe/retry/error)",
                "check_retry_limit -> (retry/fail)",
                "enhanced_kambo_response -> (continue/error)",
                "create_final_response -> END",
                "handle_error -> END"
            ],
            "conditional_edges": [
                "validate_input -> (continue/error)",
                "moderate_input -> (continue/error)",
                "check_safety -> (continue/reject)",
                "retrieve_context -> (continue/error)",
                "generate_kambo_response -> (continue/error)",
                "verify_medical -> (safe/retry/error)",
                "check_retry_limit -> (retry/fail)",
                "enhanced_kambo_response -> (continue/error)"
            ],
            "features": [
                "Input validation and sanitization",
                "Content moderation",
                "Topic safety checking",
                "RAG context retrieval",
                "Medical verification with feedback loop",
                "Retry mechanism (max 3 attempts)",
                "Enhanced response generation",
                "Comprehensive error handling"
            ]
        }
    
    def _load_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Load recent conversation history for a user"""
        try:
            session = get_session()
            
            # Get recent conversations for this user
            conversations = session.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(Conversation.started_at.desc()).limit(5).all()
            
            conversation_ids = [conv.id for conv in conversations]
            
            if not conversation_ids:
                return []
            
            # Get messages from these conversations
            messages = session.query(Message).filter(
                Message.conversation_id.in_(conversation_ids)
            ).order_by(Message.created_at.asc()).limit(limit).all()
            
            # Convert to format for AI context
            history = []
            for msg in messages:
                history.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat()
                })
            
            session.close()
            logger.info(f"Loaded {len(history)} messages from conversation history for user {user_id}")
            return history
            
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")
            return []
    
    def _extract_user_context(self, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Extract useful context from conversation history"""
        context = {
            "user_name": None,
            "topics_discussed": [],
            "preferences": [],
            "previous_questions": []
        }
        
        # Look for name mentions
        for msg in history:
            if msg["role"] == "user":
                content = msg["content"].lower()
                # Simple name extraction patterns
                if "my name is" in content:
                    name_start = content.find("my name is") + 11
                    name_end = content.find(" ", name_start)
                    if name_end == -1:
                        name_end = len(content)
                    context["user_name"] = content[name_start:name_end].strip().title()
                elif "i'm " in content and len(content.split()) <= 5:
                    # Simple "I'm Alex" pattern
                    words = content.split()
                    if len(words) >= 2 and words[0] == "i'm":
                        context["user_name"] = words[1].title()
                
                # Track topics
                if "kambo" in content:
                    context["topics_discussed"].append("kambo")
                if "ceremony" in content:
                    context["topics_discussed"].append("ceremony")
                if "matt" in content or "o'brien" in content:
                    context["topics_discussed"].append("matt_o_brien")
                
                # Track previous questions
                context["previous_questions"].append(msg["content"])
        
        return context 