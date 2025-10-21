#!/usr/bin/env python3
"""
Start the FastAPI MCP server
"""
import subprocess
import sys
import os

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.init_db import initialize_db
from src.config import DB_PATH


def main():
    # Check if database exists, if not initialize it
    if not os.path.exists(DB_PATH):
        print("Database not found. Initializing...")
        initialize_db()
    else:
        print(f"✓ Database found at {DB_PATH}")
    
    print("\n" + "="*60)
    print("Starting MCP FastAPI Server on http://localhost:8001")
    print("Upload Interface: http://localhost:8001/upload")
    print("="*60 + "\n")
    
    # Start the server
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "src.server.api:app",
        "--host", "0.0.0.0",
        "--port", "8001",
        "--reload"
    ])


if __name__ == "__main__":
    main()

