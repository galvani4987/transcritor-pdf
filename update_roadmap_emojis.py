# This is a Python script that would run in the subtask.
# It needs to read the file, do the replace, and write it back.
import os

filepath = "ROADMAP.md"
try:
    with open(filepath, 'r', encoding='utf-8') as f:
        original_content = f.read()

    new_content = original_content.replace("✅", "[x]")

    if new_content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Successfully replaced ✅ with [x] in {filepath}")
    else:
        print(f"No instances of ✅ found in {filepath}. File unchanged.")

except FileNotFoundError:
    print(f"Error: File {filepath} not found.")
except Exception as e:
    print(f"An error occurred: {e}")
