import os
import sys
import re
import json
import time
import difflib
import importlib
import importlib.util
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# ==========================================
# 1. KONFIGURACJA SYSTEMOWA (Windows Fixes)
# ==========================================
# Wyłączamy Triton i wymuszamy kompatybilność
os.environ["WBITS_USE_TRITON"] = "0"
os.environ["UNSLOTH_USE_TRITON"] = "0"
os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.environ["TORCH_CUDA_ARCH_LIST"] = "8.6"  # Dla RTX 3060


# ==========================================
# 2. MOCKOWANIE TRITONA (Zapobiega crashom na Windows)
# ==========================================
def setup_triton_mock():
    """Tworzy atrapę Tritona, która połyka wszystkie argumenty i nie powoduje błędów."""
    dummy_code = '''
class UniversalMock:
    def __init__(self, name="Mock"): self._name = name
    def __getattr__(self, item): return self
    def __call__(self, *args, **kwargs): return self # Połyka argumenty (fix dla num_warps)
    def __iter__(self): return iter([])
    def __bool__(self): return False
    def __getitem__(self, key): return self
    def __int__(self): return 1
    def __float__(self): return 1.0

_mock = UniversalMock()
def cdiv(x, y): return (x + y - 1) // y
def next_power_of_2(n): return 1
def autotune(*args, **kwargs): return lambda fn: fn
def jit(*args, **kwargs): return lambda fn: fn
def heuristics(*args, **kwargs): return lambda fn: fn
Config = _mock
compile = _mock
'''
    # Rejestracja atrapy w systemie
    dummy_name = "triton_dummy_windows.py"
    with open(dummy_name, "w", encoding="utf-8") as f: f.write(dummy_code)
    spec = importlib.util.spec_from_file_location("triton", dummy_name)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["triton"] = module
        spec.loader.exec_module(module)
        sys.modules["triton.language"] = module
        sys.modules["triton.compiler"] = module


setup_triton_mock()


# ==========================================
# 3. KLASA KOLORÓW I KONFIGURACJA
# ==========================================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


ADAPTER_PATH = "moje_ai_adaptery"  # Ścieżka do Twojego wytrenowanego modelu
DATASET_FILE = "moj_finalny_dataset.jsonl"


# ==========================================
# 4. GŁÓWNA KLASA AUDYTORA
# ==========================================
class CodeAuditor:
    def __init__(self):
        print(f"{Colors.HEADER}🕵️  Inicjalizacja Audytora AI (Tryb Inżynierski - Windows Safe)...{Colors.ENDC}")

        try:
            gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Brak"
            print(f"{Colors.BLUE}ℹ️  GPU: {gpu_name} | Torch: {torch.__version__}{Colors.ENDC}")
        except Exception:
            pass

        if not os.path.exists(ADAPTER_PATH):
            print(f"{Colors.FAIL}❌ Brak folderu '{ADAPTER_PATH}'.{Colors.ENDC}")
            sys.exit(1)

        print(f"⏳ Ładowanie modelu...")
        try:
            # 1. Pobieramy nazwę modelu bazowego z adaptera
            base_model_name = None
            adapter_config_path = os.path.join(ADAPTER_PATH, "adapter_config.json")

            if os.path.exists(adapter_config_path):
                with open(adapter_config_path, "r") as f:
                    cfg = json.load(f)
                    base_model_name = cfg.get("base_model_name_or_path")

            if not base_model_name:
                base_model_name = ADAPTER_PATH  # Jeśli nie ma configu, zakładamy, że to pełny model

            print(f"   📦 Baza: {base_model_name}")

            # 2. Konfiguracja 4-bit (BitsAndBytes) - Kluczowe dla Windows/RTX 3060
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )

            # 3. Ładowanie modelu bazowego
            self.model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True
            )

            self.tokenizer = AutoTokenizer.from_pretrained(ADAPTER_PATH, trust_remote_code=True)

            # 4. Nakładanie Adaptera (jeśli to adapter)
            if os.path.exists(adapter_config_path):
                print(f"   🔗 Łączenie adaptera LoRA...")
                self.model = PeftModel.from_pretrained(self.model, ADAPTER_PATH)

            self.model.eval()
            print(f"{Colors.GREEN}✅ Audytor gotowy.{Colors.ENDC}\n")

        except Exception as e:
            print(f"{Colors.FAIL}❌ Krytyczny błąd ładowania: {e}{Colors.ENDC}")
            sys.exit(1)

    @staticmethod
    def detect_language(filename):
        return os.path.splitext(filename)[1]

    @staticmethod
    def extract_code(text):
        """Agresywna ekstrakcja kodu z odpowiedzi modelu."""
        # Najpierw szukamy bloków markdown
        pattern = r"```(?:\w+)?(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return max(matches, key=len).strip()

        # Fallback: szukanie linii kodu
        lines = text.splitlines()
        clean = []
        is_code = False
        for line in lines:
            # Start kodu
            if line.strip().startswith(("import ", "from ", "class ", "def ", "package ", "void ")):
                is_code = True
            if is_code:
                # Koniec kodu (nagłówki markdown lub koniec pliku)
                if line.startswith("###") or line.lower().startswith("wyjaśnienie"):
                    break
                clean.append(line)

        return "\n".join(clean).strip() if clean else text.strip()

    def generate_response(self, prompt, strict_mode=False):
        """Generuje odpowiedź. Strict Mode = prawie zerowa temperatura (brak halucynacji)."""
        try:
            inputs = self.tokenizer([prompt], return_tensors="pt").to("cuda")

            # --- LOGIKA ANTY-HALUCYNACYJNA ---
            # Jeśli strict_mode=True, temperatura jest minimalna (0.05).
            # Model staje się deterministycznym inżynierem, a nie "kreatywnym pisarzem".
            current_temp = 0.05 if strict_mode else 0.2

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=4096,
                    use_cache=True,
                    temperature=current_temp,
                    repetition_penalty=1.1,
                    do_sample=True,
                    top_p=0.95
                )

            decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

            if "### Response:" in decoded:
                return decoded.split("### Response:")[-1].strip()
            return decoded.replace(prompt, "").strip()

        except Exception as e:
            print(f"{Colors.FAIL}❌ Błąd generowania: {e}{Colors.ENDC}")
            return ""

    def audit_file(self, file_path):
        print(f"\n📄 {Colors.BOLD}Analiza: {os.path.basename(file_path)}{Colors.ENDC}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            print(f"❌ Błąd odczytu: {e}");
            return

        # Tryb luźny (analiza)
        prompt = f"### Instruction:\nAnalyze the code below. Point out critical bugs (especially threading/security issues).\nCODE:\n{code[:3000]}\n### Response:\n"
        print(self.generate_response(prompt, strict_mode=False))

        if input("\n[f] Napraw / [q] Wyjdź: ").lower() == 'f':
            self.fix_loop(file_path, code)

    def fix_loop(self, file_path, original):
        print(f"\n🤖 Generuję poprawkę (Tryb Precyzyjny)...")

        # --- DYNAMICZNY PROMPTING (ANTY-HALUCYNACJA) ---
        extra_rules = ""
        # Jeśli wykryjemy threading/lock, wstrzykujemy instrukcję przeciwko deadlockom
        if "threading" in original or "Lock" in original or "lock" in original.lower():
            extra_rules = (
                "\nCRITICAL RULES FOR THREADING:"
                "\n1. Prevent Deadlocks: Do NOT access public properties (like self.balance) inside a locked method if the property getter ALSO acquires the lock."
                "\n2. Use private attributes (self._balance) directly when inside a 'with self._lock:' block."
                "\n3. Ensure atomic operations."
            )

        prompt = (
            f"### Instruction:\n"
            f"You are a Senior Software Engineer. Rewrite the code below to fix all bugs."
            f"{extra_rules}\n"
            f"Output ONLY the corrected code inside a markdown block.\n"
            f"CODE:\n{original}\n"
            f"### Response:\n"
        )

        # Używamy strict_mode=True dla generowania kodu
        raw_response = self.generate_response(prompt, strict_mode=True)
        new_code = self.extract_code(raw_response)

        if not new_code or len(new_code) < 10:
            print(f"{Colors.WARNING}⚠️ Model nie wygenerował poprawnego kodu.{Colors.ENDC}")
            return

        self.show_diff(original, new_code, file_path)

        if input("\n💾 Zapisać? (y/n): ").lower() == 'y':
            with open(file_path, 'w', encoding='utf-8') as f: f.write(new_code)
            print(f"✅ Zapisano.")
            self.save_lesson(original, new_code, "Fix", os.path.basename(file_path))

    @staticmethod
    def save_lesson(orig, fixed, instr, filename):
        try:
            data = {"instruction": instr, "input": orig, "output": fixed}
            with open(DATASET_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        except:
            pass

    @staticmethod
    def show_diff(old, new, filename):
        print(f"\n{Colors.BOLD}--- ZMIANY ---{Colors.ENDC}")
        diff = difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile='Old', tofile='New', lineterm='')
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                print(f"{Colors.GREEN}{line}{Colors.ENDC}")
            elif line.startswith('-') and not line.startswith('---'):
                print(f"{Colors.FAIL}{line}{Colors.ENDC}")
            else:
                print(line)


if __name__ == "__main__":
    try:
        auditor = CodeAuditor()
        while True:
            path = input("\n📂 Plik (lub 'q' by wyjść): ").strip('"')
            if path.lower() == 'q': break
            if os.path.exists(path):
                auditor.audit_file(path)
            else:
                print("❌ Nie znaleziono pliku.")
    except KeyboardInterrupt:
        print("\n👋")