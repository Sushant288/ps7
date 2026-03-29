import os
from google import genai

# Load from environment variable (ensure GEMINI_API_KEY is set or use a .env loader)
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    # Attempt to read from .env file manually if not in environment
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    api_key = line.split('=')[1].strip().strip("'").strip('"')
                    break
    except Exception:
        pass

client = genai.Client(api_key=api_key)
for m in client.models.list():
 print(m.name)
