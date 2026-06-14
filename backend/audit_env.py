import os
import sys

from dotenv import load_dotenv
load_dotenv('backend/.env')

key_env = os.environ.get('GEMINI_API_KEY')
print(f"GEMINI_API_KEY present in .env? {'yes' if key_env else 'no'}")
if key_env:
    print(f"key length in .env: {len(key_env)}")

sys.path.append(os.path.join(os.getcwd(), 'backend'))
try:
    from app.core.config import settings
    print(f"settings.gemini_api_key present? {'yes' if settings.gemini_api_key else 'no'}")
    if settings.gemini_api_key:
        print(f"settings.gemini_api_key length: {len(settings.gemini_api_key)}")
except Exception as e:
    print(f"Error loading settings: {e}")
