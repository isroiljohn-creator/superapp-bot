import os
import re

def unescape(match):
    escaped_string = match.group(0)
    try:
        # Decode \uXXXX and \UXXXXXXXX to unicode objects (may create surrogates)
        s = bytes(escaped_string, "utf-8").decode("unicode_escape")
        # Collapse surrogates by bouncing through utf-16
        s = s.encode("utf-16", "surrogatepass").decode("utf-16")
        return s
    except Exception as e:
        # fallback
        return escaped_string

pattern = re.compile(r'(?:\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8})+')
count = 0

for root, dirs, files in os.walk('.'):
    if '.venv' in root or 'node_modules' in root or '.git' in root or 'static' in root or 'nuvi-uz-moderator-repo' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = pattern.sub(unescape, content)
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Fixed {filepath}")
                count += 1

print(f"Fixed total {count} files.")
