from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    
    # Calendly
    calendly_api_token: str
    calendly_event_type_uri: str
    
    # Gym Info
    gym_name: str = "FitLife Gym"
    gym_trial_price: int = 99
    gym_facilities: str = "Swimming Pool, Cardio Zone, Weight Training, Yoga Studio"
    gym_location: str = "123 Fitness Street, Mumbai"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()