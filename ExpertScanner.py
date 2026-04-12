import os
import json
import hashlib
import time
import re
import requests
import sys
import subprocess
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from tqdm import tqdm
from datetime import datetime

# ==========================================
# 1. KONFIGURACJA KLUCZY
# ==========================================
# Ustaw GEMINI_API_KEY i GROQ_API_KEY jako zmienne środowiskowe lub w pliku .env
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ==========================================
# 2. ŚCIEŻKI I PRIORYTETY
# ==========================================
PATHS_CONFIG = {
    "Android": r"C:\Users\mz100\AndroidStudioProjects",
    "Python": r"C:\Users\mz100\PycharmProjects",
}

# Projekty priorytetowe (SalesBot usunięty, uczy się najpierw innych)
PRIORITY_PROJECTS = ["Synapsa", "AdvancedApp"]

DATASET_FILE = "moj_finalny_dataset_reasoning.jsonl"
TRAINER_SCRIPT = "trener_nocny.py"

IGNORE_DIRS = {
    'node_modules', 'venv', '.git', '__pycache__', '.idea', '.vscode',
    'build', 'dist', 'vendor', 'migrations', 'target', '.gradle',
    'cmake-build-debug', 'obj', 'bin', 'coverage', 'captures', 'cache',
    'test', 'tests', 'docs', 'moje_ai_adaptery', 'unsloth_compiled_cache'
}

EXTENSIONS = ('.py', '.java', '.kt', '.cs', '.js', '.cpp')

# ==========================================
# 3. SILNIKI AI
# ==========================================
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


class GeminiRotator:
    def __init__(self):
        self.models_pool = []
        self.current_index = 0
        self.active = False
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Filtrowanie modeli, które nie nadają się do kodu
            clean = [m for m in all_models if not any(x in m for x in ['vision', 'image', 'audio', 'robotics', 'nano'])]
            # Sortowanie: Lite -> Flash -> Pro
            clean.sort(key=lambda x: (0 if 'lite' in x else 1 if 'flash' in x else 2))
            self.models_pool = clean
            if self.models_pool: self.active = True
            self._load_current()
        except:
            pass

    def _load_current(self):
        if self.models_pool: self.current_model = genai.GenerativeModel(self.models_pool[self.current_index])

    def switch_model(self):
        if not self.active: return
        self.current_index = (self.current_index + 1) % len(self.models_pool)
        self._load_current()

    def ask(self, prompt):
        if not self.active: return None
        try:
            resp = self.current_model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"},
                safety_settings=SAFETY_SETTINGS
            )
            return resp.text
        except Exception as e:
            self.switch_model()
            raise e


class GroqEngine:
    def __init__(self):
        self.active = True

    def ask(self, prompt):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": "Principal Architect. Output JSON only."},
                         {"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 429: return "LIMIT"
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except:
            return "ERROR"


# ==========================================
# 4. GŁÓWNA LOGIKA SKANERA
# ==========================================
class ArchitectScanner:
    def __init__(self):
        print(f"\033[95m🧠 Skaner Finalny (Auto-Train Mode)...\033[0m")
        self.gemini = GeminiRotator()
        self.groq = GroqEngine()
        self.seen_hashes = set()
        self.stats = {"saved": 0, "naps": 0}
        self.consecutive_limits = 0  # Licznik ciągłych porażek

    def normalize_for_hash(self, content):
        return re.sub(r'\s+', '', content)

    def get_content_hash(self, content):
        return hashlib.md5(self.normalize_for_hash(content).encode('utf-8')).hexdigest()

    def load_existing_hashes(self):
        if not os.path.exists(DATASET_FILE): return
        print("📥 Wczytywanie bazy...")
        try:
            with open(DATASET_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        rec = json.loads(line)
                        raw = rec['output']
                        if "<thinking>" in raw: raw = raw.split("</thinking>")[-1].strip()
                        self.seen_hashes.add(self.get_content_hash(raw))
                    except:
                        pass
        except:
            pass
        print(f"✅ Baza zawiera {len(self.seen_hashes)} plików.")

    def clean_json(self, text):
        if not text: return None
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end != -1: return text[start:end + 1]
        return text

    def extract_dependencies(self, code, language):
        deps = []
        pattern = r'^(?:from|import)\s+([\w\.]+)' if "Python" in language else r'^import\s+([\w\.]+)'
        matches = re.findall(pattern, code, re.MULTILINE)
        return [d for d in list(set(matches)) if len(d) > 2][:15]

    def ask_ai_persistent(self, code, filename, project_name, language, pbar_obj):
        deps = self.extract_dependencies(code, language)

        prompt = f"""
        Act as a Principal Software Architect.
        Analyze code file from project "{project_name}".
        Dependencies: {", ".join(deps)}
        FILE: {filename}

        CODE:
        {code[:12000]} 

        TASK:
        1. Infer Instruction (generic, reusable).
        2. Chain of Thought (CoT): Explain architectural role.

        OUTPUT JSON:
        {{
            "instruction": "Instruction...",
            "reasoning": "Thinking...",
            "cleaned_code": "Code"
        }}
        """

        # 1. Próba Gemini (x3)
        for _ in range(3):
            try:
                raw = self.gemini.ask(prompt)
                if raw:
                    self.consecutive_limits = 0  # Reset licznika porażek
                    return json.loads(self.clean_json(raw))
            except:
                continue

        # 2. Próba Groq
        raw_groq = self.groq.ask(prompt)

        if raw_groq == "LIMIT":
            # Jeśli limit, zwiększamy licznik porażek
            self.consecutive_limits += 1

            # WARUNEK KOŃCOWY: Jeśli 5 razy z rzędu dostaliśmy limit (czyli czekaliśmy już min. 5 minut i dalej nic)
            if self.consecutive_limits >= 5:
                return "FATAL_LIMIT"

            pbar_obj.set_description(f"💤 Limit API ({self.consecutive_limits}/5). Czekam 60s...")
            self.stats["naps"] += 1
            time.sleep(60)
            # Rekurencyjne wywołanie (próbujemy jeszcze raz ten sam plik)
            return self.ask_ai_persistent(code, filename, project_name, language, pbar_obj)

        if raw_groq and raw_groq != "ERROR":
            try:
                parsed = json.loads(self.clean_json(raw_groq))
                self.consecutive_limits = 0  # Sukces, resetujemy licznik
                return parsed
            except:
                return None

        return None

    def scan_disk_smart(self):
        print("🔍 Skanowanie i sortowanie (Od Najnowszych)...")
        candidates = []
        for category, root_folder in PATHS_CONFIG.items():
            if not os.path.exists(root_folder): continue
            try:
                project_dirs = [d for d in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, d))]
            except:
                continue

            for project_name in project_dirs:
                project_path = os.path.join(root_folder, project_name)
                if project_name in IGNORE_DIRS or project_name.startswith('.'): continue

                for root, dirs, files in os.walk(project_path):
                    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                    for file in files:
                        if file.endswith(EXTENSIONS) and file not in ["Skaner.py", "Skaner_Ekspercki.py"]:
                            full_path = os.path.join(root, file)
                            try:
                                mtime = os.path.getmtime(full_path)
                                priority_score = 10000000000 if project_name in PRIORITY_PROJECTS else 0
                                candidates.append({
                                    "path": full_path,
                                    "project": project_name,
                                    "language": category,
                                    "sort_key": priority_score + mtime,
                                })
                            except:
                                pass

        candidates.sort(key=lambda x: x['sort_key'], reverse=True)
        return candidates

    def start_training(self):
        print(f"\n\033[92m🚀 Rozpoczynamy Analizę Nocną (Trening)...\033[0m")
        if os.path.exists(TRAINER_SCRIPT):
            try:
                # Uruchamiamy trenera w nowym procesie
                subprocess.run([sys.executable, TRAINER_SCRIPT], check=True)
            except Exception as e:
                print(f"❌ Błąd uruchamiania trenera: {e}")
        else:
            print(f"❌ Nie znaleziono pliku {TRAINER_SCRIPT}")

    def run(self):
        self.load_existing_hashes()
        candidates_list = self.scan_disk_smart()
        print(f"🚀 Znaleziono {len(candidates_list)} plików.")

        pbar = tqdm(candidates_list, unit="plik", desc="Analiza AI")
        for item in pbar:
            path = item['path']
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if len(content) < 50 or len(content) > 15000: continue
                if self.get_content_hash(content) in self.seen_hashes: continue

                result = self.ask_ai_persistent(content, os.path.basename(path), item['project'], item['language'],
                                                pbar)

                # SPRAWDZAMY CZY TO KONIEC
                if result == "FATAL_LIMIT":
                    print(f"\n\033[91m🛑 WYCZERPANO WSZYSTKIE LIMITY API. KOŃCZĘ SKANOWANIE.\033[0m")
                    break  # Wychodzimy z pętli skanowania

                if result and isinstance(result, dict):
                    final = f"<thinking>\n{result.get('reasoning', '')}\n</thinking>\n\n{result.get('cleaned_code', content)}"
                    with open(DATASET_FILE, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"instruction": result.get('instruction', ''), "input": "", "output": final},
                                           ensure_ascii=False) + "\n")
                    self.seen_hashes.add(self.get_content_hash(content))
                    self.stats["saved"] += 1
                    time.sleep(0.5)

                pbar.set_postfix(sav=self.stats["saved"], naps=self.stats["naps"])
            except KeyboardInterrupt:
                print("\n🛑 Zatrzymano ręcznie. Przechodzę do treningu...")
                break
            except:
                pass

        print(f"\n✅ ZAKOŃCZONO SKANOWANIE. Zapisano nowych: {self.stats['saved']}")

        # Automatyczne uruchomienie trenera po zakończeniu
        self.start_training()


if __name__ == "__main__":
    ArchitectScanner().run()