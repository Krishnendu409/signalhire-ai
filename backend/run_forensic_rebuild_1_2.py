import os
import shutil
import hashlib
import csv
from pathlib import Path

def run_phase_1_2():
    print("Running Phase 1 & 2")
    base_dir = r"C:\Users\krish\Documents\signalhire"
    val_dir = os.path.join(base_dir, "backend", "validation")
    
    dirs = ["real", "uploaded", "benchmark", "rejected", "manifests"]
    for d in dirs:
        os.makedirs(os.path.join(val_dir, d), exist_ok=True)
        
    all_pdfs = []
    for root, _, files in os.walk(base_dir):
        if '.gemini' in root or '.git' in root or 'node_modules' in root or 'venv' in root or 'backend\\validation' in root:
            continue
        for f in files:
            if f.lower().endswith('.pdf'):
                all_pdfs.append(os.path.join(root, f))
                
    # Deduplicate and classify
    seen_hashes = {}
    duplicates = []
    manifest = []
    
    for path in all_pdfs:
        try:
            with open(path, 'rb') as f:
                data = f.read()
            h = hashlib.sha256(data).hexdigest()
            size = len(data)
            
            # Simple page count (works for some PDFs, 0 if unable to parse)
            page_count = data.count(b'/Page\n') + data.count(b'/Page\r') + data.count(b'/Page ') + data.count(b'/Page/')
            
            # Classification heuristic
            source_type = "UNKNOWN"
            lp = path.lower()
            if "benchmark" in lp:
                source_type = "BENCHMARK"
            elif "upload" in lp:
                source_type = "UPLOADED"
            elif "real" in lp or "sample" in lp:
                source_type = "REAL"
            elif "generated" in lp or "synthetic" in lp:
                source_type = "GENERATED"
            else:
                source_type = "REAL" # Assume real if not specified
                
            if h in seen_hashes:
                duplicates.append({
                    "file": path,
                    "sha256": h,
                    "original": seen_hashes[h]
                })
                # Move to rejected
                dest = os.path.join(val_dir, "rejected", os.path.basename(path))
                if not os.path.exists(dest):
                    shutil.copy2(path, dest)
            else:
                seen_hashes[h] = path
                
                if source_type == "BENCHMARK" or source_type == "GENERATED":
                    dest_folder = "benchmark"
                elif source_type == "UPLOADED":
                    dest_folder = "uploaded"
                else:
                    dest_folder = "real"
                    
                dest = os.path.join(val_dir, dest_folder, os.path.basename(path))
                # Handle filename collisions
                counter = 1
                orig_dest = dest
                while os.path.exists(dest):
                    base, ext = os.path.splitext(orig_dest)
                    dest = f"{base}_{counter}{ext}"
                    counter += 1
                
                shutil.copy2(path, dest)
                
                manifest.append({
                    "sha256": h,
                    "file_size": size,
                    "page_count": page_count,
                    "source_path": path,
                    "source_type": source_type,
                    "new_path": dest
                })
        except Exception as e:
            print(f"Error processing {path}: {e}")

    # Write duplicate report
    dup_report_path = os.path.join(val_dir, "duplicate_report.csv")
    with open(dup_report_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=["file", "sha256", "original"])
        w.writeheader()
        w.writerows(duplicates)
        
    # Write manifest
    manifest_path = os.path.join(val_dir, "manifests", "validation_manifest.csv")
    with open(manifest_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=["sha256", "file_size", "page_count", "source_path", "source_type", "new_path"])
        w.writeheader()
        w.writerows(manifest)
        
    # Phase 2: Dataset Forensics
    # Generate forensics based on all PDFs processed plus the old inventory
    forensics = []
    # Let's combine the manifest and duplicates to build forensics
    all_processed = manifest + [{"source_path": d["file"], "sha256": d["sha256"], "source_type": "UNKNOWN"} for d in duplicates]
    
    # We will just iterate all PDFs found and populate forensics
    for path in all_pdfs:
        try:
            with open(path, 'rb') as f:
                h = hashlib.sha256(f.read()).hexdigest()
        except:
            continue
            
        is_dup = h in [d["sha256"] for d in duplicates]
        dup_count = len([d for d in duplicates if d["sha256"] == h])
        
        lp = path.lower()
        origin = "unknown"
        if "benchmark" in lp: origin = "benchmark"
        elif "upload" in lp: origin = "recruiter upload"
        elif "synthetic" in lp or "generated" in lp: origin = "synthetic"
        else: origin = "manually curated"
        
        forensics.append({
            "file": path,
            "sha256": h,
            "origin": origin,
            "used_in_benchmark": "benchmark" in origin.lower(),
            "used_in_real_validation": origin in ["recruiter upload", "manually curated"],
            "duplicate_count": dup_count,
            "valid_for_production_testing": not is_dup and origin in ["recruiter upload", "manually curated"]
        })
        
    forensic_path = os.path.join(base_dir, "backend", "dataset_forensics.csv")
    with open(forensic_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=["file", "sha256", "origin", "used_in_benchmark", "used_in_real_validation", "duplicate_count", "valid_for_production_testing"])
        w.writeheader()
        w.writerows(forensics)

    print(f"Phase 1 & 2 complete. Found {len(all_pdfs)} PDFs. {len(manifest)} unique, {len(duplicates)} duplicates.")
    
if __name__ == '__main__':
    run_phase_1_2()
