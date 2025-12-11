from langchain.tools import Tool
from app.config import settings
import json

# Mock gym database - in production, this would come from a real database
GYM_INFO_DATABASE = {
    "facilities": {
        "cardio_zone": {
            "equipment": ["Treadmills (15)", "Ellipticals (10)", "Rowing Machines (5)", "Spin Bikes (12)"],
            "features": "Air-conditioned, TV screens, water stations"
        },
        "strength_training": {
            "equipment": ["Free weights up to 50kg", "Cable machines", "Smith machine", "Leg press", "Chest press"],
            "features": "Olympic lifting platform, Full dumbbell rack"
        },
        "swimming_pool": {
            "details": "Olympic-size pool (50m), Separate kids pool, Heated in winter",
            "timings": "6 AM - 10 PM",
            "features": "Professional swimming coaches available"
        },
        "yoga_studio": {
            "details": "Peaceful studio with meditation area",
            "classes": "Morning yoga (7 AM), Evening yoga (6 PM), Weekend workshops",
            "features": "All equipment provided"
        },
        "amenities": ["Steam room", "Sauna", "Locker rooms", "Shower facilities", "Juice bar", "Free parking"]
    },
    "classes": [
        {"name": "HIIT Training", "timing": "Mon/Wed/Fri 6 AM, 7 PM", "level": "All levels"},
        {"name": "Zumba", "timing": "Tue/Thu/Sat 6 PM", "level": "Beginners welcome"},
        {"name": "Yoga", "timing": "Daily 7 AM, 6 PM", "level": "All levels"},
        {"name": "CrossFit", "timing": "Mon/Wed/Fri 8 AM, 5 PM", "level": "Intermediate+"},
        {"name": "Spinning", "timing": "Tue/Thu 7 AM, 8 PM", "level": "All levels"},
        {"name": "Boxing", "timing": "Mon/Thu 6 PM", "level": "All levels"}
    ],
    "trainers": [
        {"name": "Rahul Sharma", "specialization": "Strength & Bodybuilding", "experience": "8 years"},
        {"name": "Priya Patel", "specialization": "Weight Loss & Nutrition", "experience": "6 years"},
        {"name": "Amit Kumar", "specialization": "CrossFit & Functional Training", "experience": "5 years"},
        {"name": "Sneha Reddy", "specialization": "Yoga & Flexibility", "experience": "10 years"}
    ],
    "operating_hours": {
        "weekdays": "5 AM - 11 PM",
        "weekends": "6 AM - 10 PM",
        "holidays": "7 AM - 8 PM"
    },
    "membership_plans": [
        {"name": "Monthly", "price": 2500, "features": "All facilities, Group classes"},
        {"name": "Quarterly", "price": 6500, "features": "All facilities, Group classes, 2 PT sessions"},
        {"name": "Annual", "price": 20000, "features": "All facilities, Unlimited classes, 10 PT sessions, Guest passes"}
    ],
    "trial_benefits": [
        "Full gym access for 1 day",
        "1 complimentary personal training session (30 mins)",
        "Fitness assessment and body composition analysis",
        "Nutrition consultation",
        "Access to all group classes scheduled that day",
        "Free trial of all facilities including pool and steam room"
    ],
    "success_stories": [
        "Rohan lost 15kg in 3 months with our weight loss program",
        "Anita completed her first marathon after training with us",
        "Vikram gained 8kg muscle mass in 6 months",
        "Senior member Mrs. Kapoor improved her flexibility and joint health"
    ]
}

def get_gym_info_tool(query: str) -> str:
    """
    Retrieve information about the gym facilities, classes, trainers, etc.
    
    Args:
        query: What information to retrieve (facilities/classes/trainers/hours/plans/trial/success)
        
    Returns:
        JSON string with requested information
    """
    query = query.lower().strip()
    
    try:
        # Handle different query types
        if "facility" in query or "facilities" in query or "equipment" in query:
            return json.dumps({
                "topic": "facilities",
                "data": GYM_INFO_DATABASE["facilities"],
                "summary": f"{settings.gym_name} offers: {settings.gym_facilities}"
            }, indent=2)
        
        elif "class" in query or "schedule" in query:
            return json.dumps({
                "topic": "classes",
                "data": GYM_INFO_DATABASE["classes"],
                "summary": f"We offer {len(GYM_INFO_DATABASE['classes'])} different group fitness classes"
            }, indent=2)
        
        elif "trainer" in query or "coach" in query:
            return json.dumps({
                "topic": "trainers",
                "data": GYM_INFO_DATABASE["trainers"],
                "summary": f"We have {len(GYM_INFO_DATABASE['trainers'])} certified personal trainers"
            }, indent=2)
        
        elif "hour" in query or "timing" in query or "time" in query:
            return json.dumps({
                "topic": "operating_hours",
                "data": GYM_INFO_DATABASE["operating_hours"]
            }, indent=2)
        
        elif "price" in query or "plan" in query or "membership" in query or "cost" in query:
            return json.dumps({
                "topic": "membership_plans",
                "data": GYM_INFO_DATABASE["membership_plans"],
                "trial_price": settings.gym_trial_price
            }, indent=2)
        
        elif "trial" in query or "benefit" in query:
            return json.dumps({
                "topic": "trial_benefits",
                "data": GYM_INFO_DATABASE["trial_benefits"],
                "price": settings.gym_trial_price,
                "summary": f"Trial includes full gym access, PT session, and fitness assessment for ₹{settings.gym_trial_price}"
            }, indent=2)
        
        elif "success" in query or "result" in query or "testimonial" in query:
            return json.dumps({
                "topic": "success_stories",
                "data": GYM_INFO_DATABASE["success_stories"]
            }, indent=2)
        
        else:
            # Return general overview
            return json.dumps({
                "topic": "overview",
                "gym_name": settings.gym_name,
                "location": settings.gym_location,
                "trial_price": settings.gym_trial_price,
                "main_facilities": settings.gym_facilities.split(", "),
                "available_info": ["facilities", "classes", "trainers", "hours", "plans", "trial", "success_stories"]
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "message": "Error retrieving gym information"
        })

# Create LangChain tool
gym_info_tool = Tool(
    name="get_gym_information",
    description="""Use this tool to retrieve specific information about the gym.
    Useful when user asks about:
    - Facilities and equipment
    - Class schedules and types
    - Personal trainers and their specializations
    - Operating hours
    - Membership plans and pricing
    - Trial benefits and what's included
    - Success stories and testimonials
    
    Input should be the type of information needed (e.g., 'facilities', 'classes', 'trainers', etc.)
    Returns detailed JSON with the requested information.""",
    func=get_gym_info_tool
)