#!/usr/bin/env python3
"""
Simple API test script for the Kambo chatbot
"""

import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("=== Testing Kambo Chatbot API ===\n")
    
    # Test 1: Health endpoint
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
        print("   ✓ Health endpoint working")
    except Exception as e:
        print(f"   ✗ Health endpoint error: {e}")
        return False
    
    # Test 2: Root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
        print("   ✓ Root endpoint working")
    except Exception as e:
        print(f"   ✗ Root endpoint error: {e}")
        return False
    
    # Test 3: Chat endpoint
    print("\n3. Testing chat endpoint...")
    try:
        payload = {
            "message": "What is Kambo?",
            "user_id": "test_user"
        }
        
        response = requests.post(
            f"{base_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Success: {result.get('success')}")
            print(f"   Response: {result.get('response', '')[:100]}...")
            print(f"   Conversation ID: {result.get('conversation_id')}")
            print("   ✓ Chat endpoint working")
        else:
            print(f"   Error Response: {response.text}")
            print("   ✗ Chat endpoint failed")
            return False
            
    except Exception as e:
        print(f"   ✗ Chat endpoint error: {e}")
        return False
    
    print("\n=== All API tests passed! ===")
    return True

if __name__ == "__main__":
    success = test_api()
    
    if success:
        print("\n🎉 API is working correctly!")
        print("You can access the interactive docs at: http://localhost:8000/docs")
    else:
        print("\n❌ Some API tests failed.") 