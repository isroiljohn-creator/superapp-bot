import os

files_to_backup = [
    "bot_runner.py",
    "requirements.txt",
    "Procfile",
    "core/db.py",
    "core/ai.py",
    "bot/handlers.py",
    "bot/keyboards.py",
    "bot/menu.py",
    "bot/onboarding.py",
    "bot/profile.py",
    "bot/calories.py",
    "bot/admin.py",
    "bot/workout.py",
    "bot/reminders.py",
    "bot/gamification.py",
    "bot/feedback.py",
    "bot/premium.py",
    "bot/templates.py",
    "bot/referral.py"
]

output_file = "full_codebase.md"

with open(output_file, "w") as outfile:
    outfile.write("# YASHA Fitness Bot - Full Codebase\n\n")
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            outfile.write(f"## {file_path}\n")
            outfile.write("```python\n")
            with open(file_path, "r") as infile:
                outfile.write(infile.read())
            outfile.write("\n```\n\n")
        else:
            outfile.write(f"## {file_path} (NOT FOUND)\n\n")

print(f"Backup created at {os.path.abspath(output_file)}")
