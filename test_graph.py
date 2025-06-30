"""
Test script for the graph coordinator
"""

import asyncio
import sys
import os
from loguru import logger

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.langchain.coordinator import Coordinator
from src.config import settings


async def test_graph():
    """Test the graph coordinator"""
    
    logger.info("Testing Graph Coordinator...")
    
    # Initialize coordinator
    coordinator = Coordinator()
    
    # Test cases
    test_cases = [
        {
            "name": "Valid Kambo Question",
            "message": "What is a Kambo ceremony?",
            "user_id": "test_user_1",
            "expected_success": True
        },
        {
            "name": "Medical Question (should be rejected)",
            "message": "How do I treat diabetes?",
            "user_id": "test_user_2", 
            "expected_success": False
        },
        {
            "name": "Kambo Safety Question",
            "message": "What are the safety considerations for Kambo?",
            "user_id": "test_user_3",
            "expected_success": True
        },
        {
            "name": "Off-topic Question",
            "message": "What's the weather like today?",
            "user_id": "test_user_4",
            "expected_success": False
        },
        {
            "name": "Empty Message",
            "message": "",
            "user_id": "test_user_5",
            "expected_success": False
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n--- Test {i}: {test_case['name']} ---")
        logger.info(f"Input: {test_case['message']}")
        
        try:
            result = await coordinator.process_message(
                test_case["message"], 
                test_case["user_id"]
            )
            
            logger.info(f"Success: {result['success']}")
            logger.info(f"Response: {result['response'][:100]}...")
            logger.info(f"Conversation ID: {result['conversation_id']}")
            logger.info(f"Metadata: {result.get('metadata', {})}")
            
            if result.get('error'):
                logger.warning(f"Error: {result['error']}")
            
            # Check if result matches expectation
            success_match = result['success'] == test_case['expected_success']
            results.append({
                "test": test_case['name'],
                "passed": success_match,
                "expected_success": test_case['expected_success'],
                "actual_success": result['success']
            })
            
            if success_match:
                logger.success(f"✓ Test {i} PASSED")
            else:
                logger.error(f"✗ Test {i} FAILED - Expected success={test_case['expected_success']}, got {result['success']}")
                
        except Exception as e:
            logger.error(f"✗ Test {i} FAILED with exception: {e}")
            results.append({
                "test": test_case['name'],
                "passed": False,
                "error": str(e)
            })
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY")
    logger.info("="*50)
    
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    
    for result in results:
        status = "PASS" if result['passed'] else "FAIL"
        logger.info(f"{status}: {result['test']}")
        if not result['passed'] and 'error' in result:
            logger.error(f"  Error: {result['error']}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.success("🎉 All tests passed!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


async def test_graph_visualization():
    """Test the graph structure and show the flow"""
    logger.info("\n" + "="*50)
    logger.info("GRAPH STRUCTURE VISUALIZATION")
    logger.info("="*50)
    
    coordinator = Coordinator()
    
    # Show the graph structure
    logger.info("Graph Flow:")
    logger.info("1. Input Validation Node")
    logger.info("   ↓ (Edge: validation result)")
    logger.info("2. Safety Check Node (Kambo classification)")
    logger.info("   ↓ (Edge: topic relevance)")
    logger.info("3. Kambo Response Generation Node")
    logger.info("   ↓ (Edge: response quality)")
    logger.info("4. Medical Verification Node")
    logger.info("   ↓ (Edge: safety verification)")
    logger.info("5. Final Response Routing")
    
    logger.info("\nGraph built successfully!")
    logger.info(f"Graph type: {type(coordinator.graph)}")
    logger.info("Graph is ready for processing")


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    # Run tests
    async def main():
        # Test graph visualization
        await test_graph_visualization()
        
        # Test actual processing
        success = await test_graph()
        
        if success:
            logger.info("\n✅ All graph tests completed successfully!")
        else:
            logger.error("\n❌ Some tests failed!")
            sys.exit(1)
    
    asyncio.run(main()) 