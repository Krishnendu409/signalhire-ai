import os
import sys
import pkg_resources
from dotenv import load_dotenv
from google import genai

# 1. Environment Verification
env_path = 'backend/.env'
loaded = load_dotenv(env_path)
key = os.environ.get("GEMINI_API_KEY")

print("--- 1. Environment Verification ---")
print(f".env loaded: {loaded}")
print(f"Loaded from path: {os.path.abspath(env_path)}")
print(f"GEMINI_API_KEY exists: {'YES' if key else 'NO'}")
if key:
    print(f"Key prefix: {key[:8]}")
    print(f"Key length: {len(key)}")
print(f"Process: {sys.executable}\n")

# 3. SDK Verification
print("--- 3. SDK Verification ---")
def get_version(pkg):
    try:
        return pkg_resources.get_distribution(pkg).version
    except pkg_resources.DistributionNotFound:
        return "Not installed"

print(f"google-genai version: {get_version('google-genai')}")
print(f"google-generativeai version: {get_version('google-generativeai')}")
print(f"Python version: {sys.version.split(' ')[0]}\n")

# 2. Direct Gemini Connectivity Test
print("--- 2. Direct Gemini Connectivity Test ---")
if key:
    try:
        client = genai.Client(api_key=key)
        
        print("Testing gemini-2.5-flash...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Reply exactly with: API WORKS"
        )
        print(f"Output for gemini-2.5-flash: {response.text}")
        
        print("\nTesting gemini-2.5-flash-latest...")
        response2 = client.models.generate_content(
            model="gemini-2.5-flash-latest",
            contents="Reply exactly with: API WORKS"
        )
        print(f"Output for gemini-2.5-flash-latest: {response2.text}")
        
    except Exception as e:
        print(f"EXCEPTION: {type(e).__name__}: {str(e)}")
else:
    print("No key to test.")
