import os
import json
import re
import hashlib
import sys
import warnings
import torch
import importlib.util
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# ==========================================
# 1. KONFIGURACJA SYSTEMOWA (Windows Fixes)
# ==========================================
os.environ["WBITS_USE_TRITON"] = "0"
os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"
os.environ["TORCH_CUDA_ARCH_LIST"] = "8.6"
warnings.filterwarnings("ignore")


# --- MOCKOWANIE TRITONA ---
def setup_triton_mock():
    dummy_code = '''
class UniversalMock:
    def __init__(self, name="Mock"): self._name = name
    def __getattr__(self, item): return self
    def __call__(self, *args, **kwargs): return self
_mock = UniversalMock()
def cdiv(x, y): return (x + y - 1) // y
def next_power_of_2(n): return 1
Config = _mock
compile = _mock
'''
    dummy_name = "triton_dummy_scanner.py"
    with open(dummy_name, "w", encoding="utf-8") as f: f.write(dummy_code)
    spec = importlib.util.spec_from_file_location("triton", dummy_name)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["triton"] = module
        spec.loader.exec_module(module)


setup_triton_mock()

# ==========================================
# 2. KONFIGURACJA SKANOWANIA
# ==========================================
PATHS_CONFIG = {
    "Aplikacja Mobilna (Android)": r"C:\Users\mz100\AndroidStudioProjects",
    "Projekt Python (PC/Backend)": r"C:\Users\mz100\PycharmProjects",
    # "Strona WWW (PHP/HTML)": r"C:\xampp\htdocs",
}

DATASET_FILE = "moj_finalny_dataset.jsonl"
ADAPTER_PATH = "moje_ai_adaptery"  # Folder z Twoimi adapterami

IGNORE_DIRS = {
    'node_modules', 'venv', '.git', '__pycache__', '.idea', '.vscode',
    'build', 'dist', 'vendor', 'migrations', 'target', '.gradle',
    'cmake-build-debug', 'obj', 'bin', 'coverage', 'captures', 'cache',
    'test', 'tests', 'docs', 'moje_ai_adaptery'
}

EXTENSIONS = ('.py', '.php', '.js', '.java', '.kt', '.html', '.css', '.sql', '.xml', '.cpp')


class DatasetBuilder:
    def __init__(self):
        self.seen_hashes = set()
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        print("⏳ Ładowanie modelu AI do opisywania kodu...")
        try:
            base_model_name = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"

            # Próba odczytu bazy z configu adaptera
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
                print("🔗 Używam Twoich wytrenowanych adapterów LoRA.")
                self.model = PeftModel.from_pretrained(self.model, ADAPTER_PATH)

            self.model.eval()
            print("✅ Model gotowy.")

        except Exception as e:
            print(f"❌ Błąd inicjalizacji AI: {e}")
            sys.exit(1)

    def normalize_for_hash(self, content):
        return re.sub(r'\s+', '', content)

    def get_content_hash(self, content):
        clean = self.normalize_for_hash(content)
        return hashlib.md5(clean.encode('utf-8')).hexdigest()

    def load_existing_dataset(self):
        if not os.path.exists(DATASET_FILE): return

        print("📥 Sprawdzanie duplikatów w bazie...")
        count = 0
        try:
            with open(DATASET_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        record = json.loads(line)
                        h = self.get_content_hash(record['output'])
                        self.seen_hashes.add(h)
                        count += 1
                    except:
                        continue
        except:
            pass
        print(f"ℹ️  Pomijam {count} plików, które już są w bazie.")

    def scan_disk(self):
        print("🔍 Skanowanie folderów...")
        candidates = []
        for context_name, root_folder in PATHS_CONFIG.items():
            if not os.path.exists(root_folder): continue
            for root, dirs, files in os.walk(root_folder):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                for file in files:
                    # Pomijamy pliki skryptów AI
                    if file in ["Skaner.py", "Agent.py", "Trener.py", "Audytor.py"]: continue

                    if file.endswith(EXTENSIONS):
                        full_path = os.path.join(root, file)
                        candidates.append((full_path, context_name))
        return candidates

    def filter_candidates(self, candidates):
        print("🕵️  Wstępna filtracja plików...")
        valid_files = []
        for path, ctx in tqdm(candidates, unit="plik"):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if len(content) < 50 or len(content) > 30000: continue  # Limit znaków dla bezpieczeństwa

                h = self.get_content_hash(content)
                if h in self.seen_hashes: continue

                valid_files.append({
                    "path": path,
                    "content": content,
                    "context": ctx,
                    "filename": os.path.basename(path)
                })
                self.seen_hashes.add(h)
            except:
                continue

        print(f"🎯 Znaleziono {len(valid_files)} nowych plików do opisania.")
        return valid_files

    def generate_instruction(self, filename, content, context):
        # Skracamy kod do promptu
        prompt_code = content[:2000]

        prompt = f"""### Instruction:
Jesteś Senior Developerem. Analizujesz plik z projektu: {context}.
PLIK: {filename}

KOD:
{prompt_code}
...

ZADANIE:
Napisz JEDNO zdanie (instrukcję), którą wpisałby programista, aby wygenerować ten kod.
Przykład: "Napisz klasę obsługującą logowanie użytkowników w PHP."
NIE używaj cudzysłowów.

### Response:
"""
        try:
            inputs = self.tokenizer([prompt], return_tensors="pt").to("cuda")
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=64,
                    temperature=0.3,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
            if "### Response:" in decoded:
                return decoded.split("### Response:")[-1].strip()
            return decoded.replace(prompt, "").strip()
        except:
            return None

    def run(self):
        self.load_existing_dataset()
        candidates = self.scan_disk()
        new_files = self.filter_candidates(candidates)

        if not new_files:
            print("😴 Brak nowych plików.")
            return

        print("🚀 Generowanie opisów (to może chwilę potrwać)...")

        # Otwieramy plik w trybie append
        with open(DATASET_FILE, "a", encoding="utf-8") as f:
            for item in tqdm(new_files, desc="AI myśli", unit="plik"):
                instruction = self.generate_instruction(
                    item['filename'],
                    item['content'],
                    item['context']
                )

                if instruction and len(instruction) > 5:
                    record = {
                        "instruction": instruction,
                        "input": "",
                        "output": item['content']
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f.flush()

        print(f"\n✅ Gotowe! Dataset powiększony. Uruchom 'Trener.py', aby się douczyć.")


if __name__ == "__main__":
    try:
        builder = DatasetBuilder()
        builder.run()
    except KeyboardInterrupt:
        print("\n🛑 Przerwano.")
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"\n❌ Błąd: {e}")