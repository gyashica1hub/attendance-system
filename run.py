# run.py (100% Render Compatible)
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from current directory
from app import create_app

# Create app instance for gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))