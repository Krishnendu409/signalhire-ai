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
        "feature_extractor.py",
        "jd_config.py",
        "offline_embedder.py",
        "rank.py",
        "run_ranking.py",
        "create_regression_baseline.py",
        "update_baselines.py",
        "test_regression.py",
        "requirements.txt",
        "README.md",
        "RESEARCH_NOTES.md",
        "submission.csv",
    ]

    # submission_metadata.yaml lives at the repo root per the official template.
    root_files_to_include = [
        "../submission_metadata.yaml",
    ]

    dirs_to_include = [
        ("archive_v1_frozen", "archive_v1_frozen"),
        ("../frontend", "frontend")
    ]

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in files_to_include:
            if os.path.exists(f):
                zipf.write(f, f)

        for f in root_files_to_include:
            if os.path.exists(f):
                zipf.write(f, os.path.basename(f))

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
