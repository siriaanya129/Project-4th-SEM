import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

# Load the .env file. If it's not found, it won't raise an error,
# but os.getenv will then rely on actual environment variables or defaults.
load_dotenv(dotenv_path)

# --- Application Settings ---
# We'll define an object-like structure manually or just use these variables directly.
# For better organization, a simple class or a dictionary can be used.

class AppSettings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "AI Personalized Learning Platform")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./default_app.db") # Default if not in .env

    # JWT Settings
    # It's crucial that SECRET_KEY is set in your .env file for security.
    # The default here is INSECURE and only for placeholder purposes.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_default_secret_in_your_env_file")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    
    # Convert ACCESS_TOKEN_EXPIRE_MINUTES to int, with a default
    _access_token_expire_minutes_str = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080") # Default to 7 days in minutes
    try:
        ACCESS_TOKEN_EXPIRE_MINUTES: int = int(_access_token_expire_minutes_str)
    except ValueError:
        print(f"Warning: Invalid ACCESS_TOKEN_EXPIRE_MINUTES value '{_access_token_expire_minutes_str}'. Using default 10080.")
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

# Create an instance of the settings
settings = AppSettings()

# --- Optional: For direct access if you prefer not to use the class instance everywhere ---
# PROJECT_NAME = settings.PROJECT_NAME
# API_V1_STR = settings.API_V1_STR
# DATABASE_URL = settings.DATABASE_URL
# SECRET_KEY = settings.SECRET_KEY
# ALGORITHM = settings.ALGORITHM
# ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# You can add print statements here for debugging if needed:
# print(f"CONFIG: Loaded DATABASE_URL: {settings.DATABASE_URL}")
# print(f"CONFIG: Loaded SECRET_KEY: {settings.SECRET_KEY[:5]}...") # Print only a part for security