import re

with open('bot/handlers/moderator_group.py', 'r') as f:
    text = f.read()

# I will just write a python script to rewrite the two handlers inside moderator_group.py
# Actually, multi_replace_file_content is better.
