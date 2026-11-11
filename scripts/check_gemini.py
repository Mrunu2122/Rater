import sys
import os
import json
from dotenv import load_dotenv

# Load from rater/.env
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

api_key = os.environ.get("GEMINI_API_KEY")
model_name = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

print("=" * 60)
print("CHECKING GEMINI API CONFIGURATION")
print("=" * 60)
print(f"Env path: {os.path.abspath(env_path)}")
print(f"Key configured: {'YES' if api_key else 'NO'}")
print(f"Configured model: {model_name}")

if not api_key:
    print("\nERROR: GEMINI_API_KEY is not set in rater/.env.")
    print("Please add your key to rater/.env: GEMINI_API_KEY=your_key_here")
    sys.exit(1)

try:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    
    print("\nQuerying available models from Google AI Studio...")
    models = list(client.models.list())
    print(f"Successfully retrieved {len(models)} models.")
    gemini_models = [m.name for m in models if "gemini" in m.name.lower()]
    print("Available Gemini models (snippet):")
    for m in gemini_models[:10]:
        print(f"  - {m}")
        
    print(f"\nTesting 1-token probe on configured model '{model_name}'...")
    resp = client.models.generate_content(
        model=model_name,
        contents="Say OK",
        config=types.GenerateContentConfig(max_output_tokens=5, temperature=0.0)
    )
    print(f"Probe Response: '{resp.text.strip()}'")
    print("GEMINI API VERIFICATION SUCCESSFUL.")
    print("=" * 60)
except Exception as e:
    print(f"\nERROR: Failed to connect to Gemini API: {e}")
    sys.exit(1)
