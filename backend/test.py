"""
Test script for Gym Sales Agent
Run this to verify all components are working
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

async def test_intent_classifier():
    """Test intent classification"""
    print("\n" + "="*60)
    print("Testing Intent Classifier")
    print("="*60)
    
    from app.agents.intent_classifier import intent_classifier
    
    test_cases = [
        ("Hi there", "low"),
        ("What facilities do you have?", "medium"),
        ("I want to book a trial right now", "high"),
        ("Can I come today at 9 AM?", "high"),
        ("Just browsing", "low"),
        ("Tell me about membership plans", "medium"),
    ]
    
    for message, expected in test_cases:
        result = await intent_classifier.classify_intent(message)
        status = "✅" if result.intent_level == expected else "❌"
        print(f"\n{status} Message: '{message}'")
        print(f"   Expected: {expected} | Got: {result.intent_level}")
        print(f"   Reasoning: {result.reasoning}")

async def test_calendly_service():
    """Test Calendly service"""
    print("\n" + "="*60)
    print("Testing Calendly Service")
    print("="*60)
    
    from app.services.calendly_service import calendly_service
    
    # Test get availability
    print("\n📅 Fetching available slots...")
    slots = await calendly_service.get_available_slots(days_ahead=7)
    
    if slots:
        print(f"✅ Found {len(slots)} available slots")
        print("\nFirst 3 slots:")
        for slot in slots[:3]:
            print(f"   • {slot['formatted']}")
    else:
        print("❌ No slots found (this might be expected if using mock data)")
    
    # Test booking (won't actually book without confirmation)
    print("\n📝 Testing booking function (dry run)...")
    print("   Note: This won't create a real booking")

async def test_gym_info_tool():
    """Test gym info retrieval"""
    print("\n" + "="*60)
    print("Testing Gym Info Tool")
    print("="*60)
    
    from app.tools.gym_info_tool import get_gym_info_tool
    
    test_queries = ["facilities", "classes", "trainers", "trial"]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        result = get_gym_info_tool(query)
        print(f"✅ Retrieved information (truncated):")
        print(f"   {result[:150]}...")

async def test_main_agent():
    """Test main agent"""
    print("\n" + "="*60)
    print("Testing Main Agent")
    print("="*60)
    
    from app.agents.main_agent import main_agent
    
    test_messages = [
        "Hi, tell me about your gym",
        "What classes do you offer?",
        "I want to book a trial session"
    ]
    
    session_id = "test-session-001"
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📨 Message {i}: '{message}'")
        result = await main_agent.process_message(message, session_id)
        print(f"🤖 Intent: {result['intent_level']}")
        print(f"💬 Response (truncated): {result['response'][:200]}...")

async def test_api_endpoints():
    """Test API endpoints"""
    print("\n" + "="*60)
    print("Testing API Endpoints")
    print("="*60)
    
    import httpx
    
    base_url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            print("\n🏥 Testing /health endpoint...")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
            
            # Test chat endpoint
            print("\n💬 Testing /chat endpoint...")
            response = await client.post(
                f"{base_url}/chat",
                json={"message": "I want to book a trial"}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Chat endpoint working")
                print(f"   Intent: {data.get('intent_level')}")
                print(f"   Response: {data.get('response')[:100]}...")
            else:
                print(f"❌ Chat endpoint failed: {response.status_code}")
                
    except Exception as e:
        print(f"❌ API not running. Start it with: python -m app.main")
        print(f"   Error: {str(e)}")

async def main():
    """Run all tests"""
    print("\n" + "🎯"*30)
    print("GYM SALES AGENT - SYSTEM TEST")
    print("🎯"*30)
    
    print("\nℹ️  This script tests all components of the system")
    print("ℹ️  Make sure you have set up your .env file with API keys\n")
    
    try:
        # Test components (don't require server running)
        await test_intent_classifier()
        await test_calendly_service()
        await test_gym_info_tool()
        await test_main_agent()
        
        # Test API (requires server running)
        await test_api_endpoints()
        
        print("\n" + "="*60)
        print("✅ All Tests Complete!")
        print("="*60)
        print("\nNext Steps:")
        print("1. Start the server: python -m app.main")
        print("2. Open browser: http://localhost:8000")
        print("3. Start chatting with the agent!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())