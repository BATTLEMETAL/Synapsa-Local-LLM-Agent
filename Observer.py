import time
import os
import json
import hashlib
import re
import threading
import queue
import sys
import warnings
import torch
import importlib.util

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# --- KONFIGURACJA WINDOWS ---
os.environ["WBITS_USE_TRITON"] = "0"
os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"
os.environ["TORCH_CUDA_ARCH_LIST"] = "8.6"
warnings.filterwarnings("ignore")


# --- MOCKOWANIE TRITONA (Dla stabilności bitsandbytes) ---
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
    dummy_name = "triton_dummy_obs.py"
    with open(dummy_name, "w", encoding="utf-8") as f: f.write(dummy_code)
    spec = importlib.util.spec_from_file_location("triton", dummy_name)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["triton"] = module
        spec.loader.exec_module(module)


setup_triton_mock()

# --- KONFIGURACJA ŚCIEŻEK ---
# Tutaj podaj foldery, które chcesz obserwować
PATHS_CONFIG = {
    "Projekt Testowy": r"C:\Users\mz100\PycharmProjects\ProjektTestowy",
    # "Inny Projekt": r"C:\Ścieżka\Do\Projektu"
}

DATASET_FILE = "moj_finalny_dataset.jsonl"
ADAPTER_PATH = "moje_ai_adaptery"  # Ścieżka do Twoich wytrenowanych adapterów

IGNORE_DIRS = {
    'node_modules', 'venv', '.git', '__pycache__', '.idea', '.vscode',
    'build', 'dist', 'vendor', 'migrations', 'target', '.gradle',
    'obj', 'bin', 'coverage', 'captures', 'cache', '.mypy_cache',
    'moje_ai_adaptery'  # Ważne: ignoruj folder z modelem!
}

LANGUAGE_CONFIG = {
    '.py': 'python', '.php': 'php', '.js': 'javascript',
    '.java': 'java', '.kt': 'kotlin', '.html': 'html', '.css': 'css',
    '.cpp': 'cpp', '.c': 'c'
}

# Kolejka zadań
ai_queue = queue.Queue()


class LocalAIWorker(threading.Thread):
    """Wątek AI działający na lokalnym modelu (Transformers + Peft)."""

    def __init__(self):
        super().__init__(daemon=True)
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        print("⏳ AI Worker: Ładowanie modelu do VRAM (może to potrwać chwilę)...")
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

            # Tokenizer bierzemy z bazy lub adaptera
            tk_path = ADAPTER_PATH if os.path.exists(ADAPTER_PATH) else base_model_name
            self.tokenizer = AutoTokenizer.from_pretrained(tk_path, trust_remote_code=True)

            if os.path.exists(os.path.join(ADAPTER_PATH, "adapter_config.json")):
                print("🔗 Podłączanie Twoich adapterów LoRA...")
                self.model = PeftModel.from_pretrained(self.model, ADAPTER_PATH)

            self.model.eval()
            print("🤖 AI Worker: Gotowy i uzbrojony.")

        except Exception as e:
            print(f"❌ Błąd ładowania modelu: {e}")
            sys.exit(1)

    def run(self):
        while True:
            task = ai_queue.get()
            try:
                self.process_task(task)
            except Exception as e:
                print(f"❌ Błąd workera: {e}")
            finally:
                ai_queue.task_done()

    def generate_instruction(self, filename, code_snippet, context):
        prompt = f"""### Instruction:
Jesteś Senior Tech Lead. Analizujesz zmianę w pliku: {filename} (Kontekst: {context}).

KOD PO ZMIANIE:
{code_snippet[:2000]}

ZADANIE:
Napisz JEDNO krótkie zdanie w trybie rozkazującym, opisujące co robi ten kod.
Np. "Dodać obsługę błędów logowania", "Naprawić wyciek pamięci w pętli".
NIE używaj słów "Ten kod...", "Zmiana polega na...". Pisz samą instrukcję.

### Response:
"""
        try:
            inputs = self.tokenizer([prompt], return_tensors="pt").to("cuda")
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=64,  # Krótka odpowiedź
                    temperature=0.3,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
            if "### Response:" in decoded:
                return decoded.split("### Response:")[-1].strip()
            return decoded.replace(prompt, "").strip()
        except Exception as e:
            print(f"⚠️  Błąd generowania: {e}")
            return "Zaktualizuj kod."

    def process_task(self, task):
        path, content, context = task
        filename = os.path.basename(path)

        print(f"⏳ Analizuję zmianę: {filename}...")
        intent = self.generate_instruction(filename, content, context)

        # Czyszczenie odpowiedzi z ewentualnych śmieci
        intent = intent.split('\n')[0].strip('"').strip("'")

        print(f"✅ [LEKCJA] {filename} -> {intent}")

        lesson = {
            "instruction": intent,
            "input": "",  # Input pusty, bo to "coading from scratch" lub update
            "output": content
        }

        try:
            with open(DATASET_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(lesson, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"❌ Błąd zapisu pliku: {e}")


class SmartCollector(FileSystemEventHandler):
    def __init__(self):
        self.last_state = {}
        self.last_event_time = {}
        self.debounce_seconds = 2.0
        self.load_initial_snapshot()

    def normalize_code(self, code):
        code = re.sub(r'#.*', '', code)
        code = re.sub(r'//.*', '', code)
        return "".join(code.split())

    def get_logic_hash(self, content):
        return hashlib.md5(self.normalize_code(content).encode('utf-8')).hexdigest()

    def detect_context(self, file_path):
        for ctx_name, ctx_path in PATHS_CONFIG.items():
            if ctx_path in file_path: return ctx_name
        return "Projekt"

    def load_initial_snapshot(self):
        print("🔍 Indeksowanie plików (Snapshot)...")
        count = 0
        for _, root_folder in PATHS_CONFIG.items():
            if not os.path.exists(root_folder): continue
            for root, dirs, files in os.walk(root_folder):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext in LANGUAGE_CONFIG:
                        path = os.path.join(root, file)
                        try:
                            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                                self.last_state[path] = self.get_logic_hash(f.read())
                            count += 1
                        except:
                            pass
        print(f"📸 Zindeksowano {count} plików. Czekam na Twoją pracę.")

    def on_modified(self, event):
        if event.is_directory: return
        path = event.src_path
        _, ext = os.path.splitext(path)
        if ext not in LANGUAGE_CONFIG: return

        # Debounce
        now = time.time()
        last = self.last_event_time.get(path, 0)
        if now - last < self.debounce_seconds: return
        self.last_event_time[path] = now

        time.sleep(0.5)  # Czekamy na flush na dysk

        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            return

        if not content.strip(): return  # Pustych nie bierzemy

        current_hash = self.get_logic_hash(content)
        if path in self.last_state and self.last_state[path] == current_hash:
            return

        self.last_state[path] = current_hash

        # Nowe zadanie dla workera
        context = self.detect_context(path)
        ai_queue.put((path, content, context))


if __name__ == "__main__":
    # 1. Uruchamiamy model w tle
    worker = LocalAIWorker()
    worker.start()

    # 2. Uruchamiamy Watchdoga
    observer = Observer()
    handler = SmartCollector()

    active = 0
    for name, path in PATHS_CONFIG.items():
        if os.path.exists(path):
            observer.schedule(handler, path, recursive=True)
            print(f"👁️  Monitoruję: {name}")
            active += 1
        else:
            print(f"⚠️  Ścieżka nie istnieje: {path}")

    if active == 0:
        print("❌ Brak ścieżek.")
        sys.exit(0)

    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Zatrzymano.")
    observer.join()