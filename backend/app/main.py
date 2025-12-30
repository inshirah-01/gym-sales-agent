from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import uuid
from pathlib import Path

from app.config import settings
from app.models.schemas import ChatRequest, ChatResponse
from app.agents.main_agent import main_agent
from app.services.mongodb_service import mongodb_service

# Initialize FastAPI app
app = FastAPI(
    title="Gym Sales Agent API",
    description="AI-powered sales agent with conversation memory",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static files
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.on_event("startup")
async def startup_event():
    """Connect to MongoDB on startup"""
    await mongodb_service.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect from MongoDB on shutdown"""
    await mongodb_service.disconnect()

@app.get("/")
async def root():
    """Serve the frontend"""
    frontend_file = frontend_path / "index.html"
    if frontend_file.exists():
        return FileResponse(frontend_file)
    return {"message": "Gym Sales Agent API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "gym-sales-agent",
        "version": "2.0.0",
        "mongodb": "connected" if mongodb_service.client else "disconnected"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        result = await main_agent.process_message(
            user_message=request.message,
            session_id=session_id
        )
        
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            intent_level=result.get("intent_level"),
            booking_made=result.get("booking_made", False)
        )
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/{session_id}")
async def get_memory(session_id: str):
    """Get memory for a session (for debugging/viewing)"""
    try:
        memory = await mongodb_service.get_memory(session_id)
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found for this session")
        
        return {
            "success": True,
            "session_id": session_id,
            "memory": memory
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memory/{session_id}")
async def delete_memory(session_id: str):
    """Delete memory for a session"""
    try:
        success = await mongodb_service.delete_memory(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {
            "success": True,
            "message": "Memory deleted successfully",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset-session/{session_id}")
async def reset_session(session_id: str):
    """Reset a conversation session (clears chat history, keeps memory)"""
    try:
        main_agent.reset_session(session_id)
        return {
            "success": True,
            "message": "Session reset successfully (memory preserved)",
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-calendly")
async def test_calendly():
    """Test Calendly integration"""
    from app.services.calendly_service import calendly_service
    
    try:
        slots = await calendly_service.get_available_slots(days_ahead=7)
        return {
            "success": True,
            "available_slots": len(slots),
            "slots": slots[:5]  # Return first 5 slots
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/test-mongodb")
async def test_mongodb():
    """Test MongoDB connection"""
    try:
        if not mongodb_service.client:
            return {
                "success": False,
                "message": "MongoDB not connected"
            }
        
        # Try to ping MongoDB
        await mongodb_service.client.admin.command('ping')
        
        # Count documents in collection
        count = await mongodb_service.collection.count_documents({})
        
        return {
            "success": True,
            "message": "MongoDB connection healthy",
            "database": settings.mongodb_database,
            "collection": "user_memories",
            "total_memories": count
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )