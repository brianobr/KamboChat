#!/usr/bin/env python3
"""
Key Vault Setup and Testing Script

This script helps you set up and test Azure Key Vault integration for the Kambo Chatbot.
"""

import os
import sys
from typing import Optional

def check_azure_cli():
    """Check if Azure CLI is installed and user is logged in"""
    try:
        import subprocess
        result = subprocess.run(['az', 'account', 'show'], 
                              capture_output=True, text=True, check=True)
        print("✅ Azure CLI is installed and user is logged in")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Azure CLI not found or user not logged in")
        print("Please install Azure CLI and run 'az login'")
        return False

def check_environment_variables():
    """Check if required environment variables are set"""
    required_vars = ['AZURE_KEY_VAULT_URL']
    optional_vars = ['AZURE_CLIENT_ID', 'OPENAI_API_KEY', 'SECRET_KEY']
    
    print("\n🔍 Checking environment variables...")
    
    missing_required = []
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set")
            missing_required.append(var)
    
    print("\nOptional variables (for fallback):")
    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"⚠️  {var}: Not set (will use Key Vault)")
    
    return len(missing_required) == 0

def test_key_vault_connection():
    """Test Key Vault connection and secret retrieval"""
    print("\n🔐 Testing Key Vault connection...")
    
    try:
        from src.security.key_vault import get_secret, list_secrets
        
        # Test listing secrets
        secrets = list_secrets()
        if secrets:
            print(f"✅ Successfully connected to Key Vault")
            print(f"📋 Available secrets: {', '.join(secrets)}")
        else:
            print("⚠️  Connected to Key Vault but no secrets found")
        
        # Test retrieving specific secrets
        openai_key = get_secret("openai-api-key", "OPENAI_API_KEY")
        if openai_key:
            print("✅ OpenAI API key retrieved successfully")
        else:
            print("❌ OpenAI API key not found in Key Vault or environment")
        
        app_secret = get_secret("app-secret-key", "SECRET_KEY")
        if app_secret:
            print("✅ App secret key retrieved successfully")
        else:
            print("❌ App secret key not found in Key Vault or environment")
        
        return True
        
    except Exception as e:
        print(f"❌ Key Vault connection failed: {e}")
        return False

def test_application_config():
    """Test application configuration loading"""
    print("\n⚙️  Testing application configuration...")
    
    try:
        from src.config import settings
        
        print(f"✅ Configuration loaded successfully")
        print(f"📱 App Name: {settings.app_name}")
        print(f"🔑 OpenAI Model: {settings.openai_model}")
        print(f"🗄️  Database URL: {settings.database_url}")
        print(f"🔐 Secret Key: {'Set' if settings.secret_key else 'Not set'}")
        print(f"🤖 OpenAI API Key: {'Set' if settings.openai_api_key else 'Not set'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def setup_instructions():
    """Print setup instructions"""
    print("\n" + "="*60)
    print("🚀 KEY VAULT SETUP INSTRUCTIONS")
    print("="*60)
    
    print("\n1. 📋 Create Azure Key Vault:")
    print("   az keyvault create --name kambo-chatbot-vault --resource-group kambo-chatbot-rg --location eastus --sku standard")
    
    print("\n2. 🔑 Add secrets to Key Vault:")
    print("   az keyvault secret set --vault-name kambo-chatbot-vault --name openai-api-key --value 'your_openai_api_key'")
    print("   az keyvault secret set --vault-name kambo-chatbot-vault --name app-secret-key --value 'your_app_secret'")
    
    print("\n3. 🆔 Enable managed identity for App Service:")
    print("   az webapp identity assign --name kambo-chatbot-app --resource-group kambo-chatbot-rg")
    
    print("\n4. 🔐 Grant App Service access to Key Vault:")
    print("   az keyvault set-policy --name kambo-chatbot-vault --object-id <principal_id> --secret-permissions get list")
    
    print("\n5. 🌍 Set environment variables in Azure App Service:")
    print("   AZURE_KEY_VAULT_URL=https://kambo-chatbot-vault.vault.azure.net/")
    print("   AZURE_CLIENT_ID=<managed_identity_client_id>")
    
    print("\n📖 For detailed instructions, see KEY_VAULT_SETUP.md")

def main():
    """Main function"""
    print("🔐 Kambo Chatbot - Key Vault Setup and Testing")
    print("="*50)
    
    # Check prerequisites
    if not check_azure_cli():
        setup_instructions()
        return
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    # Test Key Vault connection
    kv_ok = test_key_vault_connection()
    
    # Test application configuration
    config_ok = test_application_config()
    
    # Summary
    print("\n" + "="*50)
    print("📊 SETUP SUMMARY")
    print("="*50)
    
    if env_ok and kv_ok and config_ok:
        print("🎉 All tests passed! Key Vault is properly configured.")
        print("✅ Your application is ready to use Key Vault for secure secret management.")
    else:
        print("⚠️  Some tests failed. Please review the setup instructions below.")
        setup_instructions()

if __name__ == "__main__":
    main() 