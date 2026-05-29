# run.py - Render ke liye special version
import os
import sys

# Current directory ko path mein add karo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Direct import (package ke bina)
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False)