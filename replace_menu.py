import re
import glob

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if 'main_menu_keyboard' not in content:
        return

    # Add import if needed
    if 'get_main_menu' not in content and 'main_menu_keyboard' in content:
        content = content.replace('from bot.keyboards.buttons import', 'from bot.keyboards.buttons import get_main_menu,')
        # Handle specific cases for imports
        content = re.sub(r'from bot\.keyboards\.buttons import (.*?)main_menu_keyboard(.*?)$', r'from bot.keyboards.buttons import \1get_main_menu\2', content, flags=re.MULTILINE)

    # Replace usages
    # Case 1: reply_markup=main_menu_keyboard(...)
    content = re.sub(r'main_menu_keyboard\(([^)]*)\)', r'await get_main_menu(\1)', content)
    
    # Fix double awaits if any
    content = content.replace('await await', 'await')
    
    with open(filepath, 'w') as f:
        f.write(content)

for filepath in glob.glob('bot/handlers/*.py'):
    fix_file(filepath)

print("Replacement complete.")
