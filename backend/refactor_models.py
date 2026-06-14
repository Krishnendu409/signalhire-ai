import os
import glob

models_dir = r"C:\Users\krish\Documents\signalhire\backend\app\models\*.py"
for filepath in glob.glob(models_dir):
    with open(filepath, 'r') as f:
        content = f.read()
    
    if "from sqlalchemy.dialects.postgresql import UUID, JSONB" in content:
        content = content.replace(
            "from sqlalchemy.dialects.postgresql import UUID, JSONB",
            "from sqlalchemy.types import Uuid as UUID, JSON as JSONB"
        )
    if "from sqlalchemy.dialects.postgresql import UUID" in content:
        content = content.replace(
            "from sqlalchemy.dialects.postgresql import UUID",
            "from sqlalchemy.types import Uuid as UUID"
        )
    
    with open(filepath, 'w') as f:
        f.write(content)

print("Replaced postgresql imports with cross-db types")
