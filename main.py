import requests
import os

GEMINI_API = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1/models?key={GEMINI_API}"

r = requests.get(url)
print(r.json())
