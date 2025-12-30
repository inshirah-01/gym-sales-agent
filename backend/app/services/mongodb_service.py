from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Optional, Dict
from app.config import settings

class MongoDBService:
    """
    MongoDB service for storing structured lead memory
    """
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.collection = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.db = self.client[settings.mongodb_database]
            self.collection = self.db["user_memories"]
            
            # Test connection
            await self.client.admin.command('ping')
            print("✅ MongoDB connected successfully")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            print("MongoDB disconnected")
    
    async def get_memory(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve memory for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Memory document or None if not found
        """
        try:
            memory = await self.collection.find_one({"_id": session_id})
            
            # If no memory exists, return default structure
            if not memory:
                return {
                    "_id": session_id,
                    "fitness_goals": "Unknown",
                    "past_experience": "Unknown",
                    "location_proximity": "Unknown",
                    "joining_timeline": "Unknown",
                    "motivation": "Unknown",
                    "preferred_time": "Unknown",
                    "health_physical_info": "Unknown",
                    "objections": "None",
                    "conversation_summary": "None",
                    "total_messages": 0,
                    "last_intent": "unknown",
                    "created_at": datetime.utcnow().isoformat(),
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            return memory
            
        except Exception as e:
            print(f"Error retrieving memory: {str(e)}")
            return None
    
    async def save_memory(self, session_id: str, memory_data: Dict) -> bool:
        """
        Save or update memory for a session
        
        Args:
            session_id: Session identifier
            memory_data: Dictionary with all memory fields
            
        Returns:
            Success boolean
        """
        try:
            # Ensure required fields
            memory_doc = {
                "_id": session_id,
                "fitness_goals": memory_data.get("fitness_goals", "Unknown"),
                "past_experience": memory_data.get("past_experience", "Unknown"),
                "location_proximity": memory_data.get("location_proximity", "Unknown"),
                "joining_timeline": memory_data.get("joining_timeline", "Unknown"),
                "motivation": memory_data.get("motivation", "Unknown"),
                "preferred_time": memory_data.get("preferred_time", "Unknown"),
                "health_physical_info": memory_data.get("health_physical_info", "Unknown"),
                "objections": memory_data.get("objections", "None"),
                "conversation_summary": memory_data.get("conversation_summary", "None"),
                "total_messages": memory_data.get("total_messages", 0),
                "last_intent": memory_data.get("last_intent", "unknown"),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Check if memory exists
            existing = await self.collection.find_one({"_id": session_id})
            
            if existing:
                # Preserve created_at
                memory_doc["created_at"] = existing.get("created_at")
                await self.collection.replace_one(
                    {"_id": session_id},
                    memory_doc
                )
                print(f"✅ Memory updated for session: {session_id}")
            else:
                # Create new memory
                memory_doc["created_at"] = datetime.utcnow().isoformat()
                await self.collection.insert_one(memory_doc)
                print(f"✅ Memory created for session: {session_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving memory: {str(e)}")
            return False
    
    async def delete_memory(self, session_id: str) -> bool:
        """Delete memory for a session"""
        try:
            result = await self.collection.delete_one({"_id": session_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting memory: {str(e)}")
            return False

# Singleton instance
mongodb_service = MongoDBService()