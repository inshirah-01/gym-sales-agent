import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.config import settings

class CalendlyService:
    """
    Generic Calendly service that can be easily ported to Node.js
    All methods follow standard REST API patterns
    """
    
    def __init__(self):
        self.api_token = settings.calendly_api_token
        self.event_type_uri = settings.calendly_event_type_uri
        self.base_url = "https://api.calendly.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    async def get_available_slots(self, days_ahead: int = 7) -> List[Dict]:
        """
        Get available time slots for booking
        
        Args:
            days_ahead: Number of days to look ahead for availability
            
        Returns:
            List of available time slots with datetime and formatted string
        """
        try:
            start_time = datetime.utcnow().isoformat()
            end_time = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()
            
            # Get event type details first
            async with httpx.AsyncClient() as client:
                event_response = await client.get(
                    self.event_type_uri,
                    headers=self.headers
                )
                event_response.raise_for_status()
                
                # Get available times
                params = {
                    "event_type": self.event_type_uri,
                    "start_time": start_time,
                    "end_time": end_time
                }
                
                availability_response = await client.get(
                    f"{self.base_url}/event_type_available_times",
                    headers=self.headers,
                    params=params
                )
                
                if availability_response.status_code == 200:
                    data = availability_response.json()
                    slots = []
                    
                    for item in data.get("collection", []):
                        for slot in item.get("spots", []):
                            start_dt = datetime.fromisoformat(slot["start_time"].replace("Z", "+00:00"))
                            slots.append({
                                "start_time": slot["start_time"],
                                "formatted": start_dt.strftime("%B %d, %Y at %I:%M %p"),
                                "status": slot.get("status", "available")
                            })
                    
                    return slots[:10]  # Return first 10 slots
                else:
                    # Fallback: return mock slots for testing
                    return self._generate_mock_slots(days_ahead)
                    
        except Exception as e:
            print(f"Error fetching availability: {str(e)}")
            # Return mock slots as fallback
            return self._generate_mock_slots(days_ahead)
    
    def _generate_mock_slots(self, days_ahead: int = 7) -> List[Dict]:
        """Generate mock available slots for testing"""
        slots = []
        base_time = datetime.now() + timedelta(days=1)
        
        for day in range(min(days_ahead, 3)):  # Next 3 days
            for hour in [9, 11, 14, 16]:  # 9am, 11am, 2pm, 4pm
                slot_time = base_time + timedelta(days=day, hours=hour)
                slots.append({
                    "start_time": slot_time.isoformat(),
                    "formatted": slot_time.strftime("%B %d, %Y at %I:%M %p"),
                    "status": "available"
                })
        
        return slots
    
    async def create_booking(
        self,
        email: str,
        name: str,
        start_time: str,
        timezone: str = "Asia/Kolkata"
    ) -> Dict:
        """
        Create a booking/scheduling request
        
        Args:
            email: User's email
            name: User's full name
            start_time: ISO format datetime string
            timezone: User's timezone
            
        Returns:
            Dictionary with booking details or error
        """
        try:
            payload = {
                "event_type": self.event_type_uri,
                "start_time": start_time,
                "invitee": {
                    "email": email,
                    "name": name,
                    "timezone": timezone
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/scheduling_links",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "success": True,
                        "booking_url": data.get("resource", {}).get("booking_url"),
                        "scheduled_time": start_time,
                        "message": "Booking link created successfully!"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to create booking: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating booking: {str(e)}"
            }
    
    async def cancel_booking(self, booking_uuid: str, reason: Optional[str] = None) -> Dict:
        """
        Cancel a booking (for future use)
        
        Args:
            booking_uuid: UUID of the scheduled event
            reason: Optional cancellation reason
            
        Returns:
            Success/failure dictionary
        """
        try:
            payload = {}
            if reason:
                payload["reason"] = reason
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/scheduled_events/{booking_uuid}/cancellation",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    return {
                        "success": True,
                        "message": "Booking cancelled successfully"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to cancel: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "message": f"Error cancelling booking: {str(e)}"
            }

# Singleton instance
calendly_service = CalendlyService()