from langchain.tools import StructuredTool
from langchain.pydantic_v1 import BaseModel, Field
from app.services.mongodb_service import mongodb_service
from app.agents.memory_manager import memory_manager
import json
import asyncio

class MemoryUpdateInput(BaseModel):
    """Input schema for memory update tool"""
    session_id: str = Field(description="The current session ID from the conversation")
    user_message: str = Field(description="The user's latest message")
    agent_response: str = Field(description="Your response to the user")

async def update_memory_async(
    session_id: str,
    user_message: str,
    agent_response: str
) -> str:
    """
    Update lead memory using Memory Manager Agent
    
    Args:
        session_id: Current session identifier
        user_message: User's latest message
        agent_response: Agent's response to the user
    """
    try:
        # Validate inputs
        if not session_id or session_id == "session_id_here":
            return json.dumps({
                "success": False,
                "message": "Invalid session_id. Must use actual session ID."
            })
        
        if not user_message:
            return json.dumps({
                "success": False,
                "message": "user_message is required"
            })
        
        # Fetch current memory from MongoDB
        current_memory = await mongodb_service.get_memory(session_id)
        
        # Call Memory Manager Agent to update
        updated_memory = await memory_manager.update_memory(
            current_memory=current_memory,
            user_message=user_message,
            agent_response=agent_response,
            conversation_history=""
        )
        
        # Save updated memory to MongoDB
        success = await mongodb_service.save_memory(session_id, updated_memory)
        
        if success:
            # Find updated fields
            updated_fields = []
            for k in updated_memory.keys():
                if k not in ['_id', 'created_at', 'last_updated', 'total_messages']:
                    if updated_memory.get(k) != current_memory.get(k):
                        updated_fields.append(k)
            
            return json.dumps({
                "success": True,
                "message": "Memory updated successfully",
                "updated_fields": updated_fields
            })
        else:
            return json.dumps({
                "success": False,
                "message": "Failed to save memory to database"
            })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({
            "success": False,
            "message": f"Error: {str(e)}"
        })

def update_memory_sync(session_id: str, user_message: str, agent_response: str) -> str:
    """Synchronous wrapper for async function"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        update_memory_async(session_id, user_message, agent_response)
    )

# Create LangChain StructuredTool
memory_update_tool = StructuredTool.from_function(
    func=update_memory_sync,
    name="update_lead_memory",
    description="""Update the lead's memory profile with new information.
    
    **WHEN TO USE THIS TOOL:**
    Call this tool when the user shares:
    ✅ Fitness goals or health information
    ✅ Location, schedule, or timing preferences
    ✅ Personal details (name, background, experience level)
    ✅ Objections or concerns about joining
    ✅ Timeline or urgency for starting
    ✅ Meaningful context (referrals, motivation, life events)
    
    **DO NOT USE for:**
    ❌ Simple greetings ("hi", "hello", "hey")
    ❌ Acknowledgments ("ok", "got it", "thanks", "sure")
    ❌ General questions about gym info (address, hours, facilities)
    ❌ Casual back-and-forth without new personal details
    
    **Required inputs:**
    - session_id: The current session ID (extract from conversation context)
    - user_message: The user's latest message
    - agent_response: Your response to the user
    
    The Memory Manager will preserve existing information and only update fields with new confirmed details.
    
    Returns: Success confirmation with list of updated fields.""",
    args_schema=MemoryUpdateInput
)