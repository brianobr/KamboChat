"""
LangChain chains for the Kambo chatbot
"""

from typing import Dict, Any, Optional
from langchain.chains import LLMChain
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from .llm_setup import create_kambo_llm, create_medical_verifier_llm
from .prompts import create_kambo_prompt, create_medical_verifier_prompt, create_safety_check_prompt


class KamboChain:
    """LangChain-based Kambo information chain"""
    
    def __init__(self):
        self.llm = create_kambo_llm()
        self.prompt = create_kambo_prompt()
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        logger.info("Initialized Kambo LangChain")
    
    async def process(self, question: str, user_id: str = None) -> Dict[str, Any]:
        """Process a Kambo-related question"""
        try:
            logger.info(f"Processing Kambo question for user {user_id}: {question[:50]}...")
            
            # Run the chain
            result = await self.chain.ainvoke({"question": question})
            response = result["text"].strip()
            
            logger.info(f"Generated response for user {user_id} (length: {len(response)})")
            
            return {
                "success": True,
                "response": response,
                "metadata": {
                    "model": self.llm.model_name,
                    "user_id": user_id,
                    "question_length": len(question)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in Kambo chain: {e}")
            return {
                "success": False,
                "response": "I apologize, but I encountered an error processing your question about Kambo. Please try again.",
                "error": str(e),
                "metadata": {"user_id": user_id}
            }


class MedicalVerifierChain:
    """LangChain-based medical verification chain"""
    
    def __init__(self):
        self.llm = create_medical_verifier_llm()
        self.prompt = create_medical_verifier_prompt()
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        logger.info("Initialized Medical Verifier LangChain")
    
    async def process(self, question: str, response: str, user_id: str = None) -> Dict[str, Any]:
        """Verify a response for medical compliance"""
        try:
            logger.info(f"Verifying response for user {user_id}")
            
            # Run the verification chain
            result = await self.chain.ainvoke({
                "question": question,
                "response": response
            })
            
            verified_response = result["text"].strip()
            
            # Check if the response was modified (indicating issues)
            is_safe = verified_response == response
            
            logger.info(f"Medical verification {'passed' if is_safe else 'failed'} for user {user_id}")
            
            return {
                "success": True,
                "response": verified_response,
                "is_safe": is_safe,
                "metadata": {
                    "model": self.llm.model_name,
                    "user_id": user_id,
                    "verification_passed": is_safe
                }
            }
            
        except Exception as e:
            logger.error(f"Error in medical verification chain: {e}")
            return {
                "success": False,
                "response": "I apologize, but I encountered an error during medical verification. Please consult with qualified healthcare providers.",
                "error": str(e),
                "metadata": {"user_id": user_id}
            }


class SafetyCheckChain:
    """LangChain-based safety check chain"""
    
    def __init__(self):
        self.llm = create_medical_verifier_llm()  # Use deterministic LLM for classification
        self.prompt = create_safety_check_prompt()
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        logger.info("Initialized Safety Check LangChain")
    
    async def is_kambo_related(self, question: str) -> bool:
        """Check if a question is Kambo-related"""
        try:
            result = await self.chain.ainvoke({"question": question})
            response = result["text"].strip().upper()
            
            is_related = "YES" in response
            logger.info(f"Safety check: question is {'Kambo-related' if is_related else 'not Kambo-related'}")
            
            return is_related
            
        except Exception as e:
            logger.error(f"Error in safety check chain: {e}")
            # Default to allowing the question if there's an error
            return True 