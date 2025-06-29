"""
Azure Key Vault integration for secure secret management
"""

import os
from typing import Optional
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from loguru import logger


class KeyVaultManager:
    """Manages Azure Key Vault operations for secure secret retrieval"""
    
    def __init__(self, vault_url: Optional[str] = None):
        """
        Initialize Key Vault manager
        
        Args:
            vault_url: Azure Key Vault URL (e.g., https://kv-kambohealing-scus.vault.azure.net/)
        """
        self.vault_url = vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        
        if not self.vault_url:
            logger.warning("No Key Vault URL provided. Using environment variables only.")
            self.client = None
            return
            
        try:
            # Use Managed Identity in Azure, fallback to DefaultAzureCredential
            credential = DefaultAzureCredential()
            logger.info("Using DefaultAzureCredential for Key Vault authentication")
                
            self.client = SecretClient(vault_url=self.vault_url, credential=credential)
            logger.info(f"Key Vault client initialized for: {self.vault_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Key Vault client: {e}")
            self.client = None
    
    def get_secret(self, secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret from Key Vault with fallback to environment variable
        
        Args:
            secret_name: Name of the secret in Key Vault
            fallback_env_var: Environment variable name to use as fallback
            
        Returns:
            Secret value or None if not found
        """
        # Try Key Vault first
        if self.client:
            try:
                secret = self.client.get_secret(secret_name)
                logger.debug(f"Retrieved secret '{secret_name}' from Key Vault")
                return secret.value
            except Exception as e:
                logger.warning(f"Failed to retrieve secret '{secret_name}' from Key Vault: {e}")
        
        # Fallback to environment variable
        if fallback_env_var:
            value = os.getenv(fallback_env_var)
            if value:
                logger.debug(f"Retrieved secret '{secret_name}' from environment variable '{fallback_env_var}'")
                return value
        
        logger.error(f"Secret '{secret_name}' not found in Key Vault or environment variables")
        return None
    
    def set_secret(self, secret_name: str, value: str) -> bool:
        """
        Set a secret in Key Vault (for admin operations)
        
        Args:
            secret_name: Name of the secret
            value: Secret value
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Key Vault client not initialized")
            return False
            
        try:
            self.client.set_secret(secret_name, value)
            logger.info(f"Secret '{secret_name}' set in Key Vault")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret '{secret_name}' in Key Vault: {e}")
            return False
    
    def list_secrets(self) -> list:
        """
        List all available secrets in Key Vault
        
        Returns:
            List of secret names
        """
        if not self.client:
            logger.error("Key Vault client not initialized")
            return []
            
        try:
            secrets = []
            for secret_properties in self.client.list_properties_of_secrets():
                secrets.append(secret_properties.name)
            logger.debug(f"Retrieved {len(secrets)} secrets from Key Vault")
            return secrets
        except Exception as e:
            logger.error(f"Failed to list secrets from Key Vault: {e}")
            return []


# Global Key Vault manager instance
key_vault_manager = KeyVaultManager()


def get_secret(secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get secrets from Key Vault or environment variables
    
    Args:
        secret_name: Name of the secret in Key Vault
        fallback_env_var: Environment variable name to use as fallback
        
    Returns:
        Secret value or None if not found
    """
    return key_vault_manager.get_secret(secret_name, fallback_env_var)


def set_secret(secret_name: str, value: str) -> bool:
    """
    Convenience function to set secrets in Key Vault
    
    Args:
        secret_name: Name of the secret
        value: Secret value
        
    Returns:
        True if successful, False otherwise
    """
    return key_vault_manager.set_secret(secret_name, value)


def list_secrets() -> list:
    """
    Convenience function to list all secrets in Key Vault
    
    Returns:
        List of secret names
    """
    return key_vault_manager.list_secrets() 