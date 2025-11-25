from core.ai import ai_generate_workout, ai_generate_menu
import os
from dotenv import load_dotenv

load_dotenv()

user_profile = {
    'name': 'TestUser',
    'age': 25,
    'gender': 'Erkak',
    'height': 180,
    'weight': 80,
    'goal': 'Ozish',
    'allergy': 'Yo‘q'
}

print("--- Testing Workout Generation ---")
workout = ai_generate_workout(user_profile)
print(workout[:500] + "...")

print("\n--- Testing Menu Generation ---")
menu = ai_generate_menu(user_profile)
print(menu[:500] + "...")
