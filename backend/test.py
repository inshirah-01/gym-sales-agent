import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_connection():
    # Replace with your connection string
    MONGODB_URL = "url_to_your_mongodb_instance"
    
    try:
        print("Connecting to MongoDB...")
        client = AsyncIOMotorClient(MONGODB_URL)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # List databases
        db_list = await client.list_database_names()
        print(f"📋 Available databases: {db_list}")
        
        client.close()
        print("Connection closed")
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())