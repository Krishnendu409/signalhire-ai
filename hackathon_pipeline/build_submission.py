import os
import zipfile
import shutil

def create_submission_zip():
    print("Building submission package...")
    
    # 1. Clean build artifacts if needed
    # We will just include source code.
    
    zip_name = "SignalHire_AI_Challenge_Submission.zip"
    
    files_to_include = [
        "engine.py",
        "server.py",
        "requirements.txt",
        "README.md",
        "start.bat",
        "test_engine_regression.py",
        "test_regression.py",
        "test_concurrency.py",
    ]
    
    dirs_to_include = [
        ("archive_v1_frozen", "archive_v1_frozen"),
        ("../frontend", "frontend")
    ]
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in files_to_include:
            if os.path.exists(f):
                zipf.write(f, f)
                
        for src_dir, dest_dir in dirs_to_include:
            if os.path.exists(src_dir):
                for root, dirs, files in os.walk(src_dir):
                    if "node_modules" in root or ".next" in root or "__pycache__" in root:
                        continue
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, start=os.path.dirname(src_dir))
                        if src_dir == "../frontend":
                            arcname = "frontend/" + os.path.relpath(file_path, start=src_dir)
                        zipf.write(file_path, arcname)
                        
    print(f"Created {zip_name} successfully!")

if __name__ == "__main__":
    create_submission_zip()
