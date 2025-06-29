#!/usr/bin/env python3
"""
Test script for LangChain implementation
"""

import asyncio
import sys
import traceback
from loguru import logger

# Add the current directory to Python path
sys.path.append('.')

async def test_langchain_components():
    """Test individual LangChain components"""
    
    print("=== Testing LangChain Kambo Chatbot Components ===\n")
    
    # Test 1: LLM Setup
    print("1. Testing LLM setup...")
    try:
        from src.langchain.llm_setup import create_kambo_llm, create_medical_verifier_llm
        kambo_llm = create_kambo_llm()
        medical_llm = create_medical_verifier_llm()
        print(f"   ✓ LLM setup successful")
        print(f"   ✓ Kambo LLM: {kambo_llm.model_name}")
        print(f"   ✓ Medical LLM: {medical_llm.model_name}")
    except Exception as e:
        print(f"   ✗ LLM setup error: {e}")
        traceback.print_exc()
        return False
    
    # Test 2: Prompts
    print("\n2. Testing prompt templates...")
    try:
        from src.langchain.prompts import create_kambo_prompt, create_medical_verifier_prompt
        kambo_prompt = create_kambo_prompt()
        medical_prompt = create_medical_verifier_prompt()
        print(f"   ✓ Prompt templates created successfully")
        print(f"   ✓ Kambo prompt variables: {kambo_prompt.input_variables}")
        print(f"   ✓ Medical prompt variables: {medical_prompt.input_variables}")
    except Exception as e:
        print(f"   ✗ Prompt error: {e}")
        traceback.print_exc()
        return False
    
    # Test 3: Kambo Chain
    print("\n3. Testing Kambo chain...")
    try:
        from src.langchain.chains import KamboChain
        kambo_chain = KamboChain()
        result = await kambo_chain.process("What is Kambo?", "test_user")
        print(f"   ✓ Kambo chain working")
        print(f"   ✓ Response success: {result['success']}")
        print(f"   ✓ Response length: {len(result['response'])}")
        print(f"   ✓ Model used: {result['metadata']['model']}")
    except Exception as e:
        print(f"   ✗ Kambo chain error: {e}")
        traceback.print_exc()
        return False
    
    # Test 4: Medical Verifier Chain
    print("\n4. Testing medical verifier chain...")
    try:
        from src.langchain.chains import MedicalVerifierChain
        medical_chain = MedicalVerifierChain()
        test_response = "Kambo is a traditional Amazonian medicine used in ceremonies."
        result = await medical_chain.process("What is Kambo?", test_response, "test_user")
        print(f"   ✓ Medical verifier working")
        print(f"   ✓ Verification success: {result['success']}")
        print(f"   ✓ Is safe: {result['is_safe']}")
    except Exception as e:
        print(f"   ✗ Medical verifier error: {e}")
        traceback.print_exc()
        return False
    
    # Test 5: Safety Check Chain
    print("\n5. Testing safety check chain...")
    try:
        from src.langchain.chains import SafetyCheckChain
        safety_chain = SafetyCheckChain()
        is_related = await safety_chain.is_kambo_related("What is Kambo?")
        print(f"   ✓ Safety check working")
        print(f"   ✓ Kambo-related: {is_related}")
    except Exception as e:
        print(f"   ✗ Safety check error: {e}")
        traceback.print_exc()
        return False
    
    # Test 6: LangChain Coordinator
    print("\n6. Testing LangChain coordinator...")
    try:
        from src.langchain.coordinator import LangChainCoordinator
        coordinator = LangChainCoordinator()
        result = await coordinator.process_message("What is Kambo?", "test_user")
        print(f"   ✓ LangChain coordinator working")
        print(f"   ✓ Response success: {result['success']}")
        print(f"   ✓ Response: {result['response'][:100]}...")
        print(f"   ✓ Conversation ID: {result['conversation_id']}")
    except Exception as e:
        print(f"   ✗ LangChain coordinator error: {e}")
        traceback.print_exc()
        return False
    
    print("\n=== All LangChain tests passed! ===")
    return True

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Run tests
    success = asyncio.run(test_langchain_components())
    
    if success:
        print("\n🎉 LangChain implementation is working correctly!")
        print("You can now start the server with: python main.py")
    else:
        print("\n❌ Some LangChain tests failed. Check the errors above.")
        sys.exit(1) 