#!/usr/bin/env python3
"""
Script to start the MCP FastAPI server
"""
import subprocess
import sys
from init_db import initialize_db, DB_PATH
import os

def main():
    # Check if database exists, if not initialize it
    if not os.path.exists(DB_PATH):
        print("Database not found. Initializing...")
        initialize_db()
    else:
        print(f"✓ Database found at {DB_PATH}")
    
    print("\n" + "="*50)
    print("Starting MCP FastAPI Server on http://localhost:8001")
    print("="*50 + "\n")
    
    # Start the server
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "mcp_server:app",
        "--host", "0.0.0.0",
        "--port", "8001",
        "--reload"
    ])

if __name__ == "__main__":
    main()

