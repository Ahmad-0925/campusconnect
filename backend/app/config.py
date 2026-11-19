from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    JWT_SECRET: str = "dev-secret"
    JWT_ALG: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()

CATEGORY_MAP = {
    "Cafeteria - Food Quality/Hygiene": "Cafeteria",
    "Cafeteria - High Prices": "Cafeteria",
    "Cafeteria - Limited Variety": "Cafeteria",
    "Cafeteria - Staff Behaviour": "Cafeteria",
    "Library - Books/Resources": "Library",
    "Library - Staff Availability": "Library",
    "Library - Timings": "Library",
    "Library - Seating/Study Space": "Library",
    "Lab/IT - Non-functional Computers": "Laboratory/IT",
    "Lab/IT - Internet Connectivity": "Laboratory/IT",
    "Lab/IT - Projector/Multimedia": "Laboratory/IT",
    "Lab/IT - Missing Software": "Laboratory/IT",
    "Academic - Teacher Late": "Teaching/Academic",
    "Academic - Notes Unavailable": "Teaching/Academic",
    "Academic - Poor Explanation": "Teaching/Academic",
    "Academic - Classroom Management": "Teaching/Academic",
}

DEPARTMENTS = ["Cafeteria", "Library", "Laboratory/IT", "Teaching/Academic"]
STATUSES = ["pending", "in_progress", "resolved", "rejected"]