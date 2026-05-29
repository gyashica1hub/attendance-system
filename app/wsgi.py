# wsgi.py (root folder mein)
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

application = create_app()
app = application