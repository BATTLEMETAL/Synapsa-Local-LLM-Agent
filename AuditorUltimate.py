import os
import sys
import json
import subprocess
import time
import re
import shutil
import torch
import warnings
import google.generativeai as genai
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# ==========================================
# 1. KONFIGURACJA
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ADAPTER_PATH = "moje_ai_adaptery"

MODEL_PRIORITY_LIST = [
    'gemini-2.0-flash-lite',
    'gemini-2.0-flash',
    'gemini-1.5-flash',
    'gemini-pro'
]

os.environ["WBITS_USE_TRITON"] = "0"
os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"
os.environ["TORCH_CUDA_ARCH_LIST"] = "8.6"
warnings.filterwarnings("ignore")


class Colors:
    HEADER = '\033[95m';
    BLUE = '\033[94m';
    CYAN = '\033[96m';
    GREEN = '\033[92m'
    WARNING = '\033[93m';
    FAIL = '\033[91m';
    ENDC = '\033[0m';
    BOLD = '\033[1m'


# --- MOCK TRITONA ---
def setup_triton_mock():
    dummy_code = "import sys\nclass M: __getattr__=lambda s,x:s\nsys.modules['triton']=M()"
    exec(dummy_code)


setup_triton_mock()

# --- GEMINI SETUP ---
genai.configure(api_key=GEMINI_API_KEY)
active_gemini_model = None

print(f"{Colors.BLUE}📡 Inicjalizacja Sędziego (Gemini)...{Colors.ENDC}")
for model_name in MODEL_PRIORITY_LIST:
    try:
        test_model = genai.GenerativeModel(model_name)
        active_gemini_model = test_model
        print(f"{Colors.GREEN}✅ Wybrano model: {model_name}{Colors.ENDC}")
        break
    except:
        continue

if not active_gemini_model:
    print(f"{Colors.FAIL}❌ Błąd połączenia z API.{Colors.ENDC}")
    sys.exit(1)


class ProjectAuditor:
    def __init__(self, project_root):
        print(f"{Colors.HEADER}🏗️  Inicjalizacja Audytora (Architect Mode)...{Colors.ENDC}")
        self.project_root = os.path.abspath(project_root)

    def get_project_structure(self):
        structure = []
        ignore = {'.git', 'venv', '__pycache__', '.idea', 'node_modules', 'build', 'dist', 'moje_ai_adaptery'}
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ignore]
            for file in files:
                if file.endswith(('.py', '.json', '.xml', '.java', '.kt', '.js')):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, self.project_root)
                    structure.append(rel_path)
        return structure

    def read_all_code(self):
        context = ""
        structure = self.get_project_structure()
        for rel_path in structure:
            full_path = os.path.join(self.project_root, rel_path)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) < 20000:  # Limit wielkości pojedynczego pliku dla kontekstu
                        context += f"\n--- FILE: {rel_path} ---\n{content}\n"
            except:
                pass
        return context, structure

    def run_project(self, entry_point):
        full_path = os.path.join(self.project_root, entry_point)
        print(f"⚙️  Test uruchomieniowy: {entry_point}...")
        try:
            result = subprocess.run(
                [sys.executable, full_path],
                cwd=self.project_root,
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT: Execution took too long (possible infinite loop)."
        except Exception as e:
            return False, str(e)

    def extract_json(self, text):
        try:
            match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
            if match: return json.loads(match.group(1))
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1: return json.loads(text[start:end + 1])
        except:
            pass
        return None

    def ask_architect(self, prompt_type, context, extra_info=""):
        prompts = {
            "FIX": f"""
                Act as a Principal Software Engineer. Fix the broken project.

                ERROR LOG:
                {extra_info}

                PROJECT CONTEXT:
                {context}

                TASK:
                Return a JSON object with corrected file contents.
                FORMAT: {{ "fixes": [ {{ "path": "main.py", "content": "..." }} ] }}
            """,
            "REFACTOR": f"""
                Act as a Software Architect. The current project structure is messy or could be improved.

                PROJECT CONTEXT:
                {context}

                TASK:
                Propose a better file structure and refactored code.
                Split large files into modules. Apply SOLID principles.

                FORMAT: {{ "fixes": [ {{ "path": "core/engine.py", "content": "..." }}, {{ "path": "main.py", "content": "..." }} ] }}
            """
        }

        prompt = prompts[prompt_type]

        for _ in range(3):
            try:
                response = active_gemini_model.generate_content(prompt)
                return self.extract_json(response.text)
            except Exception as e:
                time.sleep(5)
        return None

    def apply_changes(self, fixes):
        if not fixes or "fixes" not in fixes: return False

        print(f"\n🔧 Aplikuję {len(fixes['fixes'])} zmian...")
        for fix in fixes['fixes']:
            path = fix['path']
            content = fix['content']

            # Obsługa ścieżek
            abs_path = os.path.join(self.project_root, path)

            # Backup
            if os.path.exists(abs_path):
                shutil.copy(abs_path, abs_path + ".bak")

            # Tworzenie folderów jeśli nowe
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   -> Zapisano: {path}")
        return True

    def audit_and_heal(self, entry_point=None):
        print(f"\n🔍 {Colors.BOLD}AUDYT PROJEKTU: {self.project_root}{Colors.ENDC}")

        # 1. Pobieramy kod
        full_context, structure = self.read_all_code()

        if not entry_point:
            # Tryb samej restrukturyzacji (gdy nie wiemy co uruchomić)
            print("⚠️ Nie podano pliku startowego. Przechodzę do analizy statycznej.")
            choice = input("Czy chcesz, aby AI zaproponowało lepszą strukturę plików (Refactor)? [y/n]: ")
            if choice.lower() == 'y':
                fixes = self.ask_architect("REFACTOR", full_context)
                self.apply_changes(fixes)
            return

        # 2. Tryb naprawczy (Run & Fix)
        success, output = self.run_project(entry_point)

        if success:
            print(f"{Colors.GREEN}✅ Projekt działa poprawnie.{Colors.ENDC}")
            print(f"   Wyjście:\n{output[:200]}...")

            if input("\nCzy mimo to chcesz przeprowadzić Refaktoryzację Architektury? [y/n]: ").lower() == 'y':
                fixes = self.ask_architect("REFACTOR", full_context)
                self.apply_changes(fixes)
        else:
            print(f"{Colors.FAIL}❌ BŁĄD KRYTYCZNY!{Colors.ENDC}")
            print(f"📋 Log błędu:\n{output[-1000:]}")

            print(f"\n🚑 {Colors.CYAN}Wzywam Architekta do naprawy...{Colors.ENDC}")
            fixes = self.ask_architect("FIX", full_context, output)

            if self.apply_changes(fixes):
                print("\n🔄 Weryfikacja naprawy...")
                s2, o2 = self.run_project(entry_point)
                if s2:
                    print(f"{Colors.GREEN}🎉 SUKCES! Naprawiono.{Colors.ENDC}")
                else:
                    print(f"{Colors.WARNING}⚠️ Nadal błędy. Uruchom ponownie.{Colors.ENDC}")


if __name__ == "__main__":
    target_dir = input(f"\n📂 Ścieżka projektu: ").strip('"')

    if os.path.exists(target_dir):
        auditor = ProjectAuditor(target_dir)

        files = auditor.get_project_structure()
        py_files = [f for f in files if f.endswith('.py')]

        entry = None
        if py_files:
            print(f"\nZnaleziono pliki Python: {', '.join(py_files[:5])}...")
            default = "main.py" if "main.py" in py_files else py_files[0]
            entry = input(f"🚀 Plik startowy (Enter = {default}, 'skip' = sam refactor): ") or default
            if entry == 'skip': entry = None

        auditor.audit_and_heal(entry)
    else:
        print("❌ Folder nie istnieje.")