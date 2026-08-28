import os
import sys

# Ensure backend folder is in sys.path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if os.path.exists(backend_dir) and backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
