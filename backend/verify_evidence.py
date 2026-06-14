import os
import hashlib
import time

cwd = r"C:\Users\krish\Documents\signalhire\backend"

csv_files = [
    "benchmark_resume_inventory.csv",
    "rank_shift.csv",
    "skill_audit.csv",
    "experience_audit.csv",
    "education_audit.csv",
    "certification_audit.csv"
]

scripts = [
    "parser_audit.py",
    "rank_impact.py",
    "benchmark_generator.py",
    "trace_upload.py",
    "e2e_evidence.js"
]

print("==================================================")
print("STEP 1 — FILE EXISTENCE PROOF")
print("==================================================\n")
for f in csv_files:
    path = os.path.join(cwd, f)
    if os.path.exists(path):
        stat = os.stat(path)
        print(f"File: {f}")
        print(f"Absolute Path: {path}")
        print(f"Size: {stat.st_size} bytes")
        print(f"Creation: {time.ctime(stat.st_ctime)}")
        print(f"Modification: {time.ctime(stat.st_mtime)}\n")
    else:
        print(f"{f}\nFILE NOT FOUND\n")

print("==================================================")
print("STEP 2 — HASH VERIFICATION")
print("==================================================\n")
for f in csv_files:
    path = os.path.join(cwd, f)
    if os.path.exists(path):
        with open(path, "rb") as b:
            h = hashlib.sha256(b.read()).hexdigest()
        print(f"{f}: {h}")
    else:
        print(f"{f}\nFILE NOT FOUND")
print()

print("==================================================")
print("STEP 3 — ROW COUNTS")
print("==================================================\n")
for f in csv_files:
    path = os.path.join(cwd, f)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            print(f"{f}: {sum(1 for _ in file)}")
    else:
        print(f"{f}\nFILE NOT FOUND")
print()

print("==================================================")
print("STEP 4 — RANDOM ROW VALIDATION")
print("==================================================\n")
target_rows = {3, 11, 17, 23, 31, 47}
for f in csv_files:
    path = os.path.join(cwd, f)
    if os.path.exists(path):
        print(f"--- {f} ---")
        with open(path, "r", encoding="utf-8") as file:
            for i, line in enumerate(file):
                if i in target_rows:
                    print(f"Row {i}: {line.strip()}")
        print()
    else:
        print(f"{f}\nFILE NOT FOUND\n")

print("==================================================")
print("STEP 5 — SCRIPT EXISTENCE")
print("==================================================\n")
for f in scripts:
    path = os.path.join(cwd, f)
    if os.path.exists(path):
        stat = os.stat(path)
        print(f"File: {f}")
        print(f"Absolute Path: {path}")
        print(f"Size: {stat.st_size} bytes")
        print(f"Modification: {time.ctime(stat.st_mtime)}\n")
    else:
        print(f"{f}\nFILE NOT FOUND\n")

