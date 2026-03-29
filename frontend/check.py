import sys

sys.path.insert(0, '.')
from google import genai
client = genai.Client(api_key='AIzaSyCwtyc7jz3NIMBInXozFdNZGdxwjcfO2D4')
for m in client.models.list():
 print(m.name)
