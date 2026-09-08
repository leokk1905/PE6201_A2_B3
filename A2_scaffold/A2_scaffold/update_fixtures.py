#!/usr/bin/env python3
"""
Update make_fixtures_B.py with the generated EXTRA cases
"""
import os
import shutil

# Path to the files
REFERENCE_DATA_PATH = r"d:\Github\PE6201_A2\A2_reference_data\A2_reference_data"
FIXTURES_FILE = os.path.join(REFERENCE_DATA_PATH, "make_fixtures_B.py")
EXTRA_CASES_FILE = "extra_cases_for_fixtures.py"

# Read the generated extra cases
with open(EXTRA_CASES_FILE, 'r', encoding='utf-8') as f:
    extra_content = f.read()

# Read the original fixtures file
with open(FIXTURES_FILE, 'r', encoding='utf-8') as f:
    original_content = f.read()

# Find the EXTRA_* section (starts with EXTRA_SPECIALTIES and ends before def write())
start_marker = "EXTRA_SPECIALTIES = []"
end_marker = "\n\ndef write():"

start_idx = original_content.find(start_marker)
end_idx = original_content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("ERROR: Could not find EXTRA_* section in make_fixtures_B.py")
    exit(1)

# Extract the new EXTRA content from the generated file
new_extra_start = extra_content.find("# =============================================================================")
new_extra_end = extra_content.rfind("]") + 1

new_extra_section = extra_content[new_extra_start:new_extra_end]

# Build the updated content
updated_content = (
    original_content[:start_idx] +
    new_extra_section +
    original_content[end_idx:]
)

# Write the updated file
with open(FIXTURES_FILE, 'w', encoding='utf-8') as f:
    f.write(updated_content)

print(f"[OK] Updated {FIXTURES_FILE}")
print("[OK] Added 40 extra test cases")
print()
print("Next steps:")
print(f"1. cd {REFERENCE_DATA_PATH}")
print("2. python make_fixtures_B.py")
print("3. python check_my_data.py")
