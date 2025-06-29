"""
LangChain LLM setup and configuration
"""

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from loguru import logger
from src.config import settings


def create_llm(model_name: str = None, temperature: float = 0.0) -> BaseChatModel:
    """
    Create a LangChain LLM instance with proper configuration
    
    Args:
        model_name: OpenAI model name (defaults to config setting)
        temperature: Model temperature (0.0 for deterministic responses)
    
    Returns:
        Configured ChatOpenAI instance
    """
    model = model_name or settings.openai_model
    
    try:
        llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=settings.openai_api_key,
            max_tokens=1000,  # Reasonable limit for chat responses
            request_timeout=30,  # 30 second timeout
        )
        
        logger.info(f"Created LangChain LLM: {model} (temperature: {temperature})")
        return llm
        
    except Exception as e:
        logger.error(f"Failed to create LLM: {e}")
        raise


def create_kambo_llm() -> BaseChatModel:
    """Create LLM specifically configured for Kambo-related queries"""
    return create_llm(
        model_name=settings.openai_model,
        temperature=0.1  # Slightly creative for educational responses
    )


def create_medical_verifier_llm() -> BaseChatModel:
    """Create LLM specifically configured for medical verification"""
    return create_llm(
        model_name=settings.openai_model,
        temperature=0.0  # Deterministic for safety verification
    ) 