import os
import glob
import time
import csv

def run_phase1_2():
    print("Starting Phase 1 & 2")
    base_dir = r"C:\Users\krish\Documents\signalhire"
    
    extensions = ['.pdf', '.docx', '.png', '.jpg', '.jpeg', '.txt', '.jsonl']
    
    resumes = []
    
    for root, dirs, files in os.walk(base_dir):
        if '.gemini' in root or '.git' in root or 'node_modules' in root or '__pycache__' in root:
            continue
            
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in extensions:
                path = os.path.join(root, file)
                size = os.path.getsize(path)
                ctime = os.path.getctime(path)
                mtime = os.path.getmtime(path)
                
                # Heuristic for provenance
                provenance = "unknown"
                content = ""
                try:
                    if ext == '.txt':
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read(1000).lower()
                    elif ext == '.jsonl':
                        provenance = "dataset"
                except:
                    pass
                    
                if "reportlab" in content or "synthetic" in path.lower():
                    provenance = "synthetic/generated"
                elif "benchmark" in path.lower():
                    provenance = "benchmark-generated"
                elif "curated" in path.lower():
                    provenance = "human-created/curated"
                elif "upload" in path.lower():
                    provenance = "uploaded by user"
                elif ext in ['.pdf', '.docx'] and size > 0:
                    provenance = "likely human-created"
                
                # Exclude obvious non-resumes based on name/path
                if "README" in file or "requirements.txt" in file or ".log" in file or "package.json" in file:
                    continue
                if ext == '.txt' and "resume" not in file.lower() and "candidate" not in file.lower() and size < 500:
                    continue
                
                # Also exclude python scripts, etc (handled by ext)
                
                resumes.append({
                    "absolute_path": path,
                    "source": os.path.basename(root),
                    "type": ext.replace('.', ''),
                    "size_bytes": size,
                    "creation_timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ctime)),
                    "modification_timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime)),
                    "provenance": provenance
                })
                
    # Output Phase 1
    with open('real_resume_inventory.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["absolute_path", "source", "type", "size_bytes", "creation_timestamp", "modification_timestamp"])
        writer.writeheader()
        for r in resumes:
            writer.writerow({k: v for k, v in r.items() if k != 'provenance'})
            
    # Output Phase 2
    with open('dataset_provenance.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["absolute_path", "provenance"])
        writer.writeheader()
        for r in resumes:
            writer.writerow({"absolute_path": r["absolute_path"], "provenance": r["provenance"]})

    print(f"Found {len(resumes)} potential resume files.")
    
if __name__ == '__main__':
    run_phase1_2()
