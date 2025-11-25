import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"Loaded Key: {api_key[:5]}...{api_key[-3:] if api_key else 'None'}")

if not api_key:
    print("Error: GEMINI_API_KEY not found.")
    exit(1)

try:
    genai.configure(api_key=api_key)
    # Try the exact name requested, or fall back to listing if it fails
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Hello")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
