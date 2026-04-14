import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# Identify the root directory of the entire AlphaForge project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# dashboard/backend -> dashboard -> project_root
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))

SECRET_KEY = os.getenv("SECRET_KEY", "default-insecure-key-do-not-use-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

# Points to the project root outputs folder as requested
DATA_DIR = os.path.join(PROJECT_ROOT, "outputs")

REFRESH_INTERVAL_SECONDS = 180
