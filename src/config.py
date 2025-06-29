"""
Configuration management for the Kambo chatbot
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

from .security.key_vault import get_secret


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # === API Keys (from Key Vault or environment) ===
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    
    # === Database ===
    database_url: str = Field(default="sqlite:///./kambo_chatbot.db", env="DATABASE_URL")
    
    # === Application ===
    app_name: str = Field(default="Kambo Chatbot", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # === RAG System ===
    vector_db_path: str = Field(default="./data/vector_db", env="VECTOR_DB_PATH")
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    
    # === Security ===
    max_input_length: int = Field(default=2000, env="MAX_INPUT_LENGTH")
    rate_limit_per_minute: int = Field(default=10, env="RATE_LIMIT_PER_MINUTE")
    secret_key: str = Field(default="dev-secret-key", env="SECRET_KEY")
    
    # === Medical Compliance ===
    medical_disclaimer: str = Field(
        default="This information is for educational purposes only and is not intended as medical advice. Always consult with a qualified healthcare provider before making any health-related decisions.",
        env="MEDICAL_DISCLAIMER"
    )
    
    # === Allowed Sources ===
    allowed_domains: List[str] = Field(
        default=[
            "kambocowboy.com",
            "pubmed.ncbi.nlm.nih.gov",
            "scholar.google.com"
        ],
        env="ALLOWED_DOMAINS"
    )
    
    # === Hosting ===
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # === Azure Key Vault ===
    azure_key_vault_url: Optional[str] = Field(default=None, env="AZURE_KEY_VAULT_URL")
    azure_client_id: Optional[str] = Field(default=None, env="AZURE_CLIENT_ID")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_secrets_from_key_vault()
    
    def _load_secrets_from_key_vault(self):
        """Load sensitive values from Azure Key Vault with fallback to environment variables"""
        
        # Load OpenAI API key from Key Vault
        key_vault_openai_key = get_secret("openai-api-key", "OPENAI_API_KEY")
        if key_vault_openai_key:
            self.openai_api_key = key_vault_openai_key
        
        # Load secret key from Key Vault
        key_vault_secret_key = get_secret("app-secret-key", "SECRET_KEY")
        if key_vault_secret_key:
            self.secret_key = key_vault_secret_key
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create global settings instance
settings = Settings() 