"""Configuration management - loads settings from environment variables"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables. "
        "Please create a .env file with your API key."
    )

# Server Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")

# Database Configuration
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "rag_database.db")

