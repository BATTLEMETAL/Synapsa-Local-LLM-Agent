import google.generativeai as genai
import os

# Klucz API z zmiennej środowiskowej — ustaw: set GEMINI_API_KEY=twoj_klucz
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    print("⚠️  Brak GEMINI_API_KEY w zmiennych środowiskowych.")
    exit(1)
genai.configure(api_key=GEMINI_API_KEY)

print("Dostępne modele:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")