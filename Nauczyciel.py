import os
import json
import time
import requests
import sys
import subprocess
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# ==========================================
# 1. KONFIGURACJA KLUCZY
# ==========================================
# Ustaw GEMINI_API_KEY i GROQ_API_KEY jako zmienne środowiskowe lub w pliku .env
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

DATASET_FILE = "moj_finalny_dataset_reasoning.jsonl"
TRAINER_SCRIPT = "trener_nocny.py"

# ==========================================
# 2. SILNIKI AI (Skopiowane z Eksperta)
# ==========================================
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


class Colors:
    HEADER = '\033[95m';
    GREEN = '\033[92m';
    FAIL = '\033[91m';
    ENDC = '\033[0m';
    CYAN = '\033[96m'


class GeminiEngine:
    def __init__(self):
        self.active = False
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')  # Preferowany szybki
            self.active = True
        except:
            pass

    def ask(self, prompt):
        if not self.active: return None
        try:
            resp = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"},
                                               safety_settings=SAFETY_SETTINGS)
            return resp.text
        except:
            return None


class GroqEngine:
    def __init__(self):
        self.active = True

    def ask(self, prompt):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": "Principal Engineer. Output JSON only."},
                         {"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            return response.json()['choices'][0]['message']['content']
        except:
            return None


# ==========================================
# 3. GŁÓWNA LOGIKA NAUCZYCIELA
# ==========================================
class Teacher:
    def __init__(self):
        print(f"{Colors.HEADER}🎓 Nauczyciel (Single File Injector)...{Colors.ENDC}")
        self.gemini = GeminiEngine()
        self.groq = GroqEngine()

    def clean_json(self, text):
        if not text: return None
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end != -1: return text[start:end + 1]
        return text

    def process_file(self, file_path):
        if not os.path.exists(file_path):
            print(f"{Colors.FAIL}❌ Nie znaleziono pliku: {file_path}{Colors.ENDC}")
            return False

        print(f"📖 Czytam plik: {Colors.CYAN}{file_path}{Colors.ENDC}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        filename = os.path.basename(file_path)

        prompt = f"""
        Act as a Principal Software Engineer.
        I am providing you with a specific CODE EXAMPLE designed to teach Best Practices (Security, Architecture, or Patterns).

        FILE CONTENT:
        {content}

        TASK:
        1. Create a generic User Instruction that would prompt for this exact solution.
        2. Create a Chain of Thought (CoT) that explains WHY this solution is correct (e.g. why we use bcrypt instead of sha256).

        OUTPUT JSON:
        {{
            "instruction": "Generic prompt...",
            "reasoning": "1. Analysis of requirements... 2. Security considerations...",
            "cleaned_code": "The content of the file"
        }}
        """

        print("🧠 Analizuję wiedzę (Gemini/Groq)...")

        # Próba 1: Gemini
        raw = self.gemini.ask(prompt)
        if not raw:
            # Próba 2: Groq
            print("⚠️ Gemini zajęte, pytam Groq...")
            raw = self.groq.ask(prompt)

        if not raw:
            print(f"{Colors.FAIL}❌ Błąd API. Nie udało się przetworzyć.{Colors.ENDC}")
            return False

        try:
            result = json.loads(self.clean_json(raw))

            # Formujemy rekord
            final_output = f"<thinking>\n{result.get('reasoning', '')}\n</thinking>\n\n{result.get('cleaned_code', content)}"
            record = {
                "instruction": result.get('instruction', ''),
                "input": "",
                "output": final_output
            }

            # Zapisujemy do datasetu
            with open(DATASET_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

            print(f"{Colors.GREEN}✅ SUKCES! Wiedza dodana do bazy.{Colors.ENDC}")
            return True

        except Exception as e:
            print(f"{Colors.FAIL}❌ Błąd zapisu: {e}{Colors.ENDC}")
            return False

    def run_trainer(self):
        print(f"\n{Colors.HEADER}🔥 Czy chcesz natychmiast uruchomić trening?{Colors.ENDC}")
        print("To 'wypali' nową wiedzę w modelu. (Może zająć 1-2h)")
        choice = input("Uruchomić trenera? [y/n]: ").lower()

        if choice == 'y':
            if os.path.exists(TRAINER_SCRIPT):
                subprocess.run([sys.executable, TRAINER_SCRIPT])
            else:
                print("❌ Brak pliku trenera.")


if __name__ == "__main__":
    teacher = Teacher()

    # Tryb interaktywny
    while True:
        target = input(f"\n📂 Podaj ścieżkę do pliku (lub 'q' by wyjść): ").strip('"')
        if target.lower() == 'q': break

        if teacher.process_file(target):
            # Po udanym dodaniu pytamy o kolejny lub trening
            continue

    # Na koniec sesji pytamy o trening
    teacher.run_trainer()