import os
import sys
import json
import torch
import warnings
import re
import difflib
import google.generativeai as genai
import importlib.util
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# ==========================================
# 1. KONFIGURACJA
# ==========================================
# Klucz API z zmiennej środowiskowej (ustaw GEMINI_API_KEY w .env lub systemie)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

ADAPTER_PATH = "moje_ai_adaptery"
DATASET_FILE = "moj_finalny_dataset.jsonl"

# Fixy systemowe dla Windows
os.environ["WBITS_USE_TRITON"] = "0"
os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"
os.environ["TORCH_CUDA_ARCH_LIST"] = "8.6"
warnings.filterwarnings("ignore")


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


# ==========================================
# 2. MOCK TRITON (WINDOWS FIX)
# ==========================================
def setup_triton_mock():
    dummy_code = '''
class UniversalMock:
    def __init__(self, name="Mock"): self._name = name
    def __getattr__(self, item): return self
    def __call__(self, *args, **kwargs): return self
_mock = UniversalMock()
def cdiv(x, y): return (x + y - 1) // y
def next_power_of_2(n): return 1
def autotune(*args, **kwargs): return lambda fn: fn
def jit(*args, **kwargs): return lambda fn: fn
Config = _mock
compile = _mock
'''
    dummy_name = "triton_dummy_hybrid.py"
    with open(dummy_name, "w", encoding="utf-8") as f: f.write(dummy_code)
    spec = importlib.util.spec_from_file_location("triton", dummy_name)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["triton"] = module
        spec.loader.exec_module(module)


setup_triton_mock()

# ==========================================
# 3. INTELIGENTNY SETUP GEMINI (AUTO-SELECT)
# ==========================================
genai.configure(api_key=GEMINI_API_KEY)


def get_best_gemini_model():
    """Wybiera najlepszy model z Twojego konta (Ze zdjęcia)."""
    print(f"{Colors.BLUE}📡 Łączenie z Google w celu pobrania listy modeli...{Colors.ENDC}")
    try:
        # Pobieramy wszystkie dostępne modele
        all_models = genai.list_models()
        available_names = [m.name.replace("models/", "") for m in all_models if
                           'generateContent' in m.supported_generation_methods]

        # --- NOWA LISTA PRIORYTETÓW (Na podstawie Twojego zdjęcia) ---
        priority_list = [
            'gemini-flash-latest',  # <--- Najlepszy balans (Szybki + Stabilny)
            'gemini-3-pro-preview',  # <--- Najmądrzejszy (ale może mieć limity)
            'gemini-2.0-flash',  # Starszy Flash (bardzo stabilny)
            'gemini-1.5-flash',  # Klasyk
            'gemini-pro'
        ]

        selected_model_name = None

        # Szukamy pierwszego pasującego
        for priority in priority_list:
            if priority in available_names:
                selected_model_name = priority
                break

        # Jeśli nie znaleziono nic z listy priorytetów, bierzemy cokolwiek co działa
        if not selected_model_name and available_names:
            selected_model_name = available_names[0]

        if selected_model_name:
            print(f"{Colors.GREEN}✅ Sędzia wybrany: {Colors.BOLD}{selected_model_name}{Colors.ENDC}")

            generation_config = {
                "temperature": 0.1,
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }
            return genai.GenerativeModel(model_name=selected_model_name, generation_config=generation_config)
        else:
            print(f"{Colors.FAIL}❌ Nie znaleziono żadnych modeli generatywnych.{Colors.ENDC}")
            return None

    except Exception as e:
        print(f"{Colors.FAIL}⚠️ Błąd połączenia z API Google: {e}{Colors.ENDC}")
        return None


# Inicjalizacja Sędziego
judge_model = get_best_gemini_model()


# ==========================================
# 4. GŁÓWNA KLASA AUDYTORA
# ==========================================
class HybridAuditor:
    def __init__(self):
        print(f"{Colors.HEADER}🕵️  Inicjalizacja Hybrydowego Audytora...{Colors.ENDC}")

        self.model = None
        self.tokenizer = None

        try:
            print("⏳ Ładowanie Twojego modelu lokalnego (Qwen + LoRA)...")
            base_model_name = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"

            if os.path.exists(os.path.join(ADAPTER_PATH, "adapter_config.json")):
                with open(os.path.join(ADAPTER_PATH, "adapter_config.json"), 'r') as f:
                    cfg = json.load(f)
                    base_model_name = cfg.get("base_model_name_or_path", base_model_name)

            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )

            self.model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True
            )

            tk_path = ADAPTER_PATH if os.path.exists(ADAPTER_PATH) else base_model_name
            self.tokenizer = AutoTokenizer.from_pretrained(tk_path, trust_remote_code=True)

            if os.path.exists(os.path.join(ADAPTER_PATH, "adapter_config.json")):
                print("🔗 Podłączanie Twojej wiedzy (Adaptery LoRA)...")
                self.model = PeftModel.from_pretrained(self.model, ADAPTER_PATH)

            self.model.eval()
            print(f"{Colors.GREEN}✅ Twój model lokalny jest gotowy.{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.FAIL}❌ Błąd inicjalizacji modelu lokalnego: {e}{Colors.ENDC}")
            sys.exit(1)

    def extract_code(self, text):
        pattern = r"```(?:\w+)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return max(matches, key=len).strip()
        if "### Response:" in text:
            text = text.split("### Response:")[-1]
        return text.strip()

    def generate_local(self, code_snippet, instructions="Fix bugs, optimize code and apply best practices."):
        prompt = f"""### Instruction:
You are an Expert Developer. {instructions}
Return ONLY the corrected code block.

CODE:
{code_snippet}

### Response:
"""
        inputs = self.tokenizer([prompt], return_tensors="pt").to("cuda")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=2048,
                temperature=0.2,
                repetition_penalty=1.1,
                do_sample=True
            )

        decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
        return self.extract_code(decoded)

    def verify_with_gemini(self, original_code, local_fix):
        if not judge_model:
            print(f"{Colors.FAIL}❌ Brak połączenia z Gemini (nie zainicjowano modelu).{Colors.ENDC}")
            return local_fix

        print(f"{Colors.CYAN}✨ Wzywam Sędziego (Google Gemini)...{Colors.ENDC}")

        prompt = f"""
        Act as a Principal Software Engineer and Security Auditor.

        TASK: Compare the ORIGINAL CODE with the PROPOSED FIX.

        ORIGINAL CODE:
        {original_code}

        PROPOSED FIX (by a Junior AI):
        {local_fix}

        INSTRUCTIONS:
        1. Check for logic bugs, hallucinations, security flaws, and best practices.
        2. If the Proposed Fix is PERFECT, return it exactly as is.
        3. If the Proposed Fix has ANY issues or can be optimized, write the BEST POSSIBLE version.

        OUTPUT:
        Return ONLY the final, clean Code block inside markdown backticks. 
        Do not write explanations outside the code block.
        """
        try:
            resp = judge_model.generate_content(prompt)
            return self.extract_code(resp.text)
        except Exception as e:
            print(f"{Colors.FAIL}⚠️ Błąd Gemini podczas generowania: {e}{Colors.ENDC}")
            return local_fix

    def show_diff(self, old, new, title="ZMIANY"):
        print(f"\n{Colors.BOLD}--- {title} ---{Colors.ENDC}")
        diff = difflib.unified_diff(
            old.splitlines(), new.splitlines(),
            fromfile='Oryginał', tofile='Nowy', lineterm=''
        )
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                print(f"{Colors.GREEN}{line}{Colors.ENDC}")
            elif line.startswith('-') and not line.startswith('---'):
                print(f"{Colors.FAIL}{line}{Colors.ENDC}")
            else:
                print(line)

    def audit_file(self, file_path):
        print(f"\n📄 {Colors.BOLD}Analiza: {os.path.basename(file_path)}{Colors.ENDC}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except:
            print("❌ Błąd odczytu pliku.");
            return

        # 1. Lokalna analiza
        print("🤖 Twój model analizuje kod...")
        local_fix = self.generate_local(code)
        self.show_diff(code, local_fix, title="PROPOZYCJA TWOJEGO MODELU")

        print(
            f"\n{Colors.BLUE}[f]{Colors.ENDC} Zastosuj lokalną  |  {Colors.CYAN}[v]{Colors.ENDC} Weryfikuj z Gemini  |  {Colors.FAIL}[q]{Colors.ENDC} Pomiń")
        choice = input(">>> Wybór: ").lower()

        final_code = local_fix
        source = "Local"

        if choice == 'v':
            better_fix = self.verify_with_gemini(code, local_fix)
            norm_local = "".join(local_fix.split())
            norm_gemini = "".join(better_fix.split())

            if norm_gemini != norm_local:
                print(f"\n{Colors.CYAN}✨ Gemini wprowadziło poprawki!{Colors.ENDC}")
                self.show_diff(local_fix, better_fix, title="KOREKTA MISTRZA (GEMINI)")
                final_code = better_fix
                source = "Gemini"
            else:
                print(f"{Colors.GREEN}✅ Gemini zatwierdza: Twój model spisał się na medal!{Colors.ENDC}")

            confirm = input(f"💾 Zapisać wersję ({source})? [y/n]: ").lower()
            if confirm != 'y': return

        elif choice == 'f':
            pass
        else:
            return

        # Zapis i Nauka
        try:
            import shutil
            shutil.copy(file_path, file_path + ".bak")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(final_code)
            print(f"{Colors.GREEN}✅ Zapisano zmiany w pliku.{Colors.ENDC}")

            lesson = {
                "instruction": "Fix bugs, optimize and apply clean code principles.",
                "input": code,
                "output": final_code
            }
            with open(DATASET_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(lesson, ensure_ascii=False) + "\n")
            print(f"🎓 Wiedza zapisana w bazie datasetu. (Źródło wiedzy: {source})")

        except Exception as e:
            print(f"❌ Błąd zapisu: {e}")


if __name__ == "__main__":
    auditor = HybridAuditor()
    print("\n💡 Podaj ścieżkę do pliku, który chcesz naprawić (np. main.py).")
    while True:
        try:
            path = input(f"\n📂 {Colors.BOLD}Ścieżka do pliku (lub 'q' aby wyjść): {Colors.ENDC}").strip('"')
            if path.lower() == 'q': break
            if os.path.exists(path) and os.path.isfile(path):
                auditor.audit_file(path)
            else:
                print("⚠️ Plik nie istnieje.")
        except KeyboardInterrupt:
            print("\n👋 Do widzenia!")
            break