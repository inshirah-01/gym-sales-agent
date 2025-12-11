from tools.calendly_tool import get_booking_link

def sales_agent(user_message: str, intent: str) -> str:
    """
    Main sales agent. Behaves based on:
    - intent (high / low)
    - direct user request for trial/demo → bypass intent and trigger Calendly
    """

    # Direct trial booking detection
    trial_keywords = ["trial", "demo", "book", "schedule", "try", "meeting"]
    if any(word in user_message.lower() for word in trial_keywords):
        link = get_booking_link()
        return f"Sure! You can book your trial here:\n{link}"

    # Intent-based personality
    if intent == "high":
        return (
            "Great! It sounds like you're really exploring this. "
            "Let me help you understand the product better and share useful insights."
        )

    return (
        "I understand you may have doubts. Let me clarify the value and help you make an informed decision."
    )
