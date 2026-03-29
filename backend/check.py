import sys
sys.path.insert(0, '.')

from google import genai

client = genai.Client(api_key='YOUR_KEY_HERE')
for m in client.models.list():
    print(m.name)
