import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Budge"
    PROJECT_VERSION: str = "1.0.0"
    DATABASE_URL: str = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("No DATABASE_URL set for Flask application")

settings = Settings()