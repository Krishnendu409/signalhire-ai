import os
import shutil
import json

base_dir = r"C:\Users\krish\Documents\signalhire"
dataset_dir = os.path.join(base_dir, "[PUB] India_runs_data_and_ai_challenge", "India_runs_data_and_ai_challenge")
gold_dir = os.path.join(base_dir, "backend", "gold_dataset")

# 1. Copy competition files
shutil.copy(os.path.join(dataset_dir, "sample_candidates.json"), os.path.join(gold_dir, "sample_candidates.json"))
shutil.copy(os.path.join(dataset_dir, "candidates.jsonl"), os.path.join(gold_dir, "candidates.jsonl"))
shutil.copy(os.path.join(dataset_dir, "job_description.docx"), os.path.join(gold_dir, "competition_jd.docx"))
shutil.copy(os.path.join(dataset_dir, "sample_submission.csv"), os.path.join(gold_dir, "competition_validation_target.csv"))

# 2. Create diverse JDs for cross-domain validation
jds = {
    "jd_data_scientist.json": {
        "title": "Data Scientist",
        "domain_knowledge": "Machine Learning",
        "must_have_experience": "5 years",
        "required_hard_skills": ["Python", "SQL", "Machine Learning", "Pandas", "Scikit-Learn"]
    },
    "jd_embedded_engineer.json": {
        "title": "Embedded Systems Engineer",
        "domain_knowledge": "Hardware",
        "must_have_experience": "3 years",
        "required_hard_skills": ["C", "C++", "RTOS", "Microcontrollers", "SPI", "I2C"]
    },
    "jd_manufacturing_engineer.json": {
        "title": "Manufacturing Engineer",
        "domain_knowledge": "Manufacturing",
        "must_have_experience": "7 years",
        "required_hard_skills": ["CAD", "Lean Manufacturing", "Six Sigma", "PLC", "SolidWorks"]
    }
}

for filename, jd_data in jds.items():
    with open(os.path.join(gold_dir, filename), "w") as f:
        json.dump(jd_data, f, indent=2)

print("Gold dataset assembled successfully.")
