from langchain.tools import Tool
from app.services.calendly_service import calendly_service
import json

async def get_available_slots_tool(days_ahead: str = "7") -> str:
    """
    Get available time slots for gym trial booking
    
    Args:
        days_ahead: Number of days to look ahead (default: 7)
        
    Returns:
        JSON string with available slots
    """
    try:
        days = int(days_ahead)
        slots = await calendly_service.get_available_slots(days)
        
        if not slots:
            return json.dumps({
                "success": False,
                "message": "No available slots found in the specified time range"
            })
        
        # Format slots for easy reading
        formatted_slots = []
        for i, slot in enumerate(slots, 1):
            formatted_slots.append(f"{i}. {slot['formatted']}")
        
        return json.dumps({
            "success": True,
            "available_slots": slots,
            "formatted_list": formatted_slots,
            "message": f"Found {len(slots)} available slots"
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error fetching slots: {str(e)}"
        })

async def book_trial_slot_tool(
    email: str,
    name: str,
    slot_time: str
) -> str:
    """
    Book a gym trial slot for a user
    
    Args:
        email: User's email address
        name: User's full name
        slot_time: ISO format datetime string or formatted time from available slots
        
    Returns:
        JSON string with booking confirmation or error
    """
    try:
        result = await calendly_service.create_booking(
            email=email,
            name=name,
            start_time=slot_time
        )
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error creating booking: {str(e)}"
        })

# Create LangChain tools
get_availability_tool = Tool(
    name="get_available_slots",
    description="""Use this tool to check available time slots for gym trial bookings. 
    Call this when user asks about availability or when you want to show them booking options.
    Input should be number of days to look ahead (default 7).
    Returns a list of available time slots.""",
    func=lambda x: get_available_slots_tool(x)
)

book_trial_tool = Tool(
    name="book_gym_trial",
    description="""Use this tool to book a gym trial slot for a user.
    ONLY use this after:
    1. User has confirmed they want to book
    2. You have collected their email and full name
    3. You have shown them available slots and they've chosen one
    
    Input must be a JSON string with keys: email, name, slot_time
    Example: {"email": "user@email.com", "name": "John Doe", "slot_time": "2024-01-15T09:00:00"}
    
    Returns booking confirmation with URL.""",
    func=lambda x: book_trial_tool(**json.loads(x))
)