from langchain.tools import Tool
from app.services.calendly_service import calendly_service
import json
import asyncio

# ============= GET AVAILABLE SLOTS =============

def get_available_slots_sync(days_ahead: str = "7") -> str:
    """Get available time slots for gym trial booking"""
    try:
        days = int(days_ahead)
        
        # Run async function in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        slots = loop.run_until_complete(calendly_service.get_available_slots(days))
        
        if not slots:
            return json.dumps({
                "success": False,
                "message": "No available slots found"
            })
        
        formatted_slots = []
        for i, slot in enumerate(slots, 1):
            formatted_slots.append(f"{i}. {slot['formatted']}")
        
        return json.dumps({
            "success": True,
            "available_slots": slots,
            "formatted_list": formatted_slots,
            "message": f"Found {len(slots)} available slots"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error: {str(e)}"
        })

# ============= BOOK TRIAL SLOT =============

def book_trial_slot_sync(booking_data: str) -> str:
    """Book a gym trial slot - input must be JSON string"""
    try:
        data = json.loads(booking_data)
        
        email = data.get("email")
        name = data.get("name")
        slot_time = data.get("slot_time")
        
        if not all([email, name, slot_time]):
            return json.dumps({
                "success": False,
                "message": "Missing required fields: email, name, or slot_time"
            })
        
        # Run async function in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            calendly_service.create_booking(
                email=email,
                name=name,
                start_time=slot_time
            )
        )
        
        return json.dumps(result, indent=2)
        
    except json.JSONDecodeError:
        return json.dumps({
            "success": False,
            "message": "Invalid JSON. Use format: {\"email\": \"...\", \"name\": \"...\", \"slot_time\": \"...\"}"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Booking error: {str(e)}"
        })

# ============= CREATE TOOLS =============

get_availability_tool = Tool(
    name="get_available_slots",
    description="Check available time slots for gym trial bookings. Input: number of days to look ahead (default 7). Returns list of available slots.",
    func=get_available_slots_sync
)

book_trial_tool = Tool(
    name="book_gym_trial",
    description="Book a gym trial slot. Input MUST be a single JSON string: '{\"email\": \"user@email.com\", \"name\": \"Full Name\", \"slot_time\": \"2024-12-18T09:00:00\"}'. Only use after user confirms booking.",
    func=book_trial_slot_sync
)