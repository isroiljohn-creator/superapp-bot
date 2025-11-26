import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")

if not api_key:
    exit(1)

genai.configure(api_key=api_key)

print("Attempting to list models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Found model: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nAttempting generation with gemini-1.5-flash...")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say Hello")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error with 1.5-flash: {e}")

print("\nAttempting generation with gemini-pro...")
try:
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Say Hello")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error with gemini-pro: {e}")
