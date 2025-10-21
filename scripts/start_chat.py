#!/usr/bin/env python3
"""
Start the Chainlit chainlit_app interface
"""
import subprocess
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("\n" + "="*60)
    print("Starting Chainlit Chat Interface on http://localhost:8000")
    print("="*60 + "\n")
    
    # Start Chainlit
    subprocess.run([
        sys.executable, "-m", "chainlit",
        "run", "src/chainlit_app/app.py",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])


if __name__ == "__main__":
    main()

