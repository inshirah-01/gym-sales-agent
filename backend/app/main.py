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

# Initialize FastAPI app
app = FastAPI(
    title="Gym Sales Agent API",
    description="AI-powered sales agent for gym trial bookings",
    version="1.0.0"
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

@app.get("/")
async def root():
    """Serve the frontend"""
    frontend_file = frontend_path / "index.html"
    if frontend_file.exists():
        return FileResponse(frontend_file)
    return {"message": "Gym Sales Agent API is running. Frontend not found."}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "gym-sales-agent",
        "version": "1.0.0"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint
    
    Receives user messages and returns agent responses with intent classification
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process the message
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

@app.post("/reset-session/{session_id}")
async def reset_session(session_id: str):
    """Reset a conversation session"""
    try:
        main_agent.reset_session(session_id)
        return {"message": "Session reset successfully", "session_id": session_id}
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

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )