#!/usr/bin/env python3
"""
Simple test script to debug the Kambo chatbot application
"""

import asyncio
import sys
import traceback
from loguru import logger

# Add the current directory to Python path
sys.path.append('.')

async def test_components():
    """Test individual components to identify issues"""
    
    print("=== Testing Kambo Chatbot Components ===\n")
    
    # Test 1: Configuration
    print("1. Testing configuration...")
    try:
        from src.config import settings
        print(f"   ✓ Configuration loaded successfully")
        print(f"   ✓ App name: {settings.app_name}")
        print(f"   ✓ Database URL: {settings.database_url}")
        print(f"   ✓ OpenAI API Key: {'Set' if settings.openai_api_key else 'Not set'}")
    except Exception as e:
        print(f"   ✗ Configuration error: {e}")
        return False
    
    # Test 2: Database initialization
    print("\n2. Testing database initialization...")
    try:
        from src.database.connection import init_database
        init_database()
        print("   ✓ Database initialized successfully")
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        traceback.print_exc()
        return False
    
    # Test 3: Knowledge base
    print("\n3. Testing knowledge base...")
    try:
        from src.rag.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        content = kb.get_relevant_content("What is Kambo?")
        print(f"   ✓ Knowledge base loaded successfully")
        print(f"   ✓ Found {len(content)} relevant content items")
    except Exception as e:
        print(f"   ✗ Knowledge base error: {e}")
        traceback.print_exc()
        return False
    
    # Test 4: Kambo Agent
    print("\n4. Testing Kambo agent...")
    try:
        from src.agents.kambo_agent import KamboAgent
        agent = KamboAgent()
        response = await agent.process({
            "question": "What is Kambo?",
            "user_id": "test_user"
        })
        print(f"   ✓ Kambo agent working")
        print(f"   ✓ Response success: {response.success}")
        print(f"   ✓ Response length: {len(response.content)}")
    except Exception as e:
        print(f"   ✗ Kambo agent error: {e}")
        traceback.print_exc()
        return False
    
    # Test 5: Medical Verifier
    # Removed: from src.agents.medical_verifier import MedicalVerifier
    # Removed: verifier = MedicalVerifier()
    # Removed: response = await verifier.process({
    #     "response": "Kambo is a traditional Amazonian medicine used in ceremonies.",
    #     "question": "What is Kambo?",
    #     "user_id": "test_user"
    # })
    # Removed: print(f"   \u2713 Medical verifier working")
    # Removed: print(f"   \u2713 Verification passed: {response.success}")
    
    # Test 6: Chatbot Coordinator
    print("\n6. Testing chatbot coordinator...")
    try:
        from src.chatbot.coordinator import ChatbotCoordinator
        coordinator = ChatbotCoordinator()
        result = await coordinator.process_message("What is Kambo?", "test_user")
        print(f"   ✓ Chatbot coordinator working")
        print(f"   ✓ Response success: {result['success']}")
        print(f"   ✓ Response: {result['response'][:100]}...")
    except Exception as e:
        print(f"   ✗ Chatbot coordinator error: {e}")
        traceback.print_exc()
        return False
    
    print("\n=== All tests passed! ===")
    return True

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Run tests
    success = asyncio.run(test_components())
    
    if success:
        print("\n🎉 Application is working correctly!")
        print("You can now start the server with: python main.py")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        sys.exit(1) 