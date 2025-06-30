#!/usr/bin/env python3
"""
Test script for Azure deployment
"""

import requests
import json
import sys
from typing import Dict, Any

# Azure app URL (replace with your actual URL)
AZURE_URL = "https://app-kambochat-cus-fsfgb9asfzf5dufj.centralus-01.azurewebsites.net"

def test_endpoint(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> bool:
    """Test a specific endpoint"""
    url = f"{AZURE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
            
        if response.status_code == 200:
            print(f"✅ {method} {endpoint} - Status: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                print(f"   Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"❌ {method} {endpoint} - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - Connection Error: {e}")
        return False

def main():
    """Main testing function"""
    print("🧪 Testing Azure Deployment...")
    print(f"📍 URL: {AZURE_URL}")
    print("=" * 50)
    
    tests = [
        ("/", "GET"),
        ("/health", "GET"),
        ("/docs", "GET"),
        ("/gradio", "GET"),
        ("/chat", "POST", {"message": "What is Kambo?", "user_id": "test_user"})
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if len(test) == 2:
            endpoint, method = test
            success = test_endpoint(endpoint, method)
        else:
            endpoint, method, data = test
            success = test_endpoint(endpoint, method, data)
        
        if success:
            passed += 1
        
        print("-" * 30)
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Deployment is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the deployment logs.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 