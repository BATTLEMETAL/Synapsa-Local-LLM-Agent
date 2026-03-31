import os
import shutil
import random
import re
import sys
import json
import torch
import warnings
import importlib.util
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# --- FIX DLA WINDOWS I TRITONA ---
os.environ["WBITS_USE_TRITON"] = "0"
os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"
os.environ["TORCH_CUDA_ARCH_LIST"] = "8.6"  # RTX 3060

warnings.filterwarnings("ignore")


# --- MOCKOWANIE TRITONA (Dla stabilności bitsandbytes na Windows) ---
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
    dummy_name = "triton_dummy_agent.py"
    with open(dummy_name, "w", encoding="utf-8") as f: f.write(dummy_code)
    spec = importlib.util.spec_from_file_location("triton", dummy_name)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["triton"] = module
        spec.loader.exec_module(module)


setup_triton_mock()


class SmartAgent:
    def __init__(self, adapter_path, target_project, context_window=4096):
        print(f"⏳ Inicjalizacja Agenta AI (Target: {target_project})...")
        self.target_project = target_project
        self.context_window = context_window

        if not os.path.exists(adapter_path):
            print(f"❌ Nie znaleziono adapterów: {adapter_path}")
            # Fallback - jeśli nie ma adapterów, spróbujmy załadować samą bazę (jeśli użytkownik poda nazwę bazy zamiast ścieżki)
            self.model_name = adapter_path
            self.is_adapter = False
        else:
            self.model_name = adapter_path
            self.is_adapter = True

        try:
            # 1. Ustalenie modelu bazowego
            base_model_name = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"  # Domyślna baza

            if self.is_adapter:
                config_path = os.path.join(adapter_path, "adapter_config.json")
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        cfg = json.load(f)
                        base_model_name = cfg.get("base_model_name_or_path", base_model_name)
                print(f"📦 Baza: {base_model_name}")
            else:
                base_model_name = self.model_name

            # 2. Konfiguracja 4-bit z CPU offload (dla RTX 3060 z ograniczonym VRAM)
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                llm_int8_enable_fp32_cpu_offload=True,  # KLUCZOWE: offload overflow na CPU RAM
            )

            # 3. ᐚdowanie z obsługą braku VRAM
            print("⏳ ᐚdowanie wag do VRAM (z CPU offload fallback)...")
            try:
                self.model = AutoModelForCausalLM.from_pretrained(
                    base_model_name,
                    quantization_config=bnb_config,
                    device_map="auto",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
                print("✅ Model załadowany na GPU.")
            except (ValueError, RuntimeError) as vram_err:
                print(f"⚠️  GPU OOM — próba 2/3: balanced_low_0 (GPU+CPU split)...")
                try:
                    self.model = AutoModelForCausalLM.from_pretrained(
                        base_model_name,
                        quantization_config=bnb_config,
                        device_map="balanced_low_0",
                        trust_remote_code=True,
                        low_cpu_mem_usage=True,
                        max_memory={0: "4GiB", "cpu": "16GiB"},
                    )
                    print("✅ Model załadowany (GPU+CPU split).")
                except (ValueError, RuntimeError) as vram_err2:
                    print(f"⚠️  GPU+CPU split też zawiodło — próba 3/3: czysty CPU float16...")
                    self.model = AutoModelForCausalLM.from_pretrained(
                        base_model_name,
                        device_map="cpu",
                        torch_dtype=torch.float16,
                        trust_remote_code=True,
                        low_cpu_mem_usage=True,
                    )
                    print("✅ Model załadowany na CPU (wolniejszy, ale działa).")

            # Ładowanie tokenizera z adaptera (jeśli istnieje) lub bazy
            tokenizer_path = adapter_path if self.is_adapter else base_model_name
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=True)

            # 4. Nakładanie LoRA
            if self.is_adapter:
                print("🔗 Podłączanie adapterów LoRA...")
                self.model = PeftModel.from_pretrained(self.model, adapter_path)

            self.model.eval()
            print("✅ Agent Gotowy.")

        except Exception as e:
            raise RuntimeError(f"Błąd inicjalizacji modelu: {e}")

    def get_files(self):
        extensions = ('.py', '.php', '.java', '.kt', '.js', '.html', '.css', '.cpp')
        # Ignorujemy venv, .git, ale też sam folder Agenta żeby nie analizował siebie w kółko
        ignore_dirs = {'venv', '.git', 'node_modules', '__pycache__', 'build', '.idea', 'dist', 'moje_ai_adaptery'}

        file_list = []
        for root, dirs, filenames in os.walk(self.target_project):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for f in filenames:
                if f.endswith(extensions):
                    # Pomijamy pliki skryptów Agenta/Trenera/Audytora
                    if f in ["Agent.py", "Trener.py", "Audytor.py", "Skaner.py"]:
                        continue
                    file_list.append(os.path.join(root, f))

        random.shuffle(file_list)
        return file_list

    def count_tokens(self, text):
        return len(self.tokenizer(text).input_ids)

    def extract_code_block(self, response):
        """Inteligentne wyciąganie kodu."""
        pattern = r"```(?:\w+)?\n(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return max(matches, key=len).strip()

        # Fallback - szukanie kodu bez markdown
        lines = response.splitlines()
        code_lines = []
        is_code = False
        for line in lines:
            if line.strip().startswith(("import ", "class ", "def ", "function ", "<?php")):
                is_code = True
            if is_code:
                if line.startswith("###") or line.lower().startswith("wyjaśnienie"): break
                code_lines.append(line)

        return "\n".join(code_lines).strip() if code_lines else None

    def ask_brain(self, prompt, max_new_tokens=2048, mode: str = "creative"):
        """
        Zadaj pytanie modelowi AI.

        Tryby:
          'creative' — Skrypty YouTube Shorts, tytuły, opisy.
                       Wyższa temperatura = większa różnorodność.
                       Silne repetition_penalty = brak pętli zdań.
          'code'     — Analiza kodu, generacja kodu, audyt.
                       Niska temperatura = precyzja i deterministyczność.
        """
        messages = [
            {"role": "user", "content": prompt}
        ]
        formatted_prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer([formatted_prompt], return_tensors="pt").to("cuda")

        # === PARAMETRY WG TRYBU ===
        if mode == "creative":
            # Tryb kreatywny dla skryptów YouTube Shorts
            gen_kwargs = dict(
                max_new_tokens=max_new_tokens,
                use_cache=True,
                temperature=0.75,          # Wystarczająco losowe żeby nie powtarzać
                repetition_penalty=1.35,   # MOCNY penalty — blokuje pętle zdań
                no_repeat_ngram_size=4,    # Zakaz powtarzania 4-gramów (zdań)
                do_sample=True,
                top_p=0.92,
                top_k=50,
            )
        else:
            # Tryb precyzyjny dla code review / analizy
            gen_kwargs = dict(
                max_new_tokens=max_new_tokens,
                use_cache=True,
                temperature=0.15,
                repetition_penalty=1.15,
                no_repeat_ngram_size=3,
                do_sample=True,
                top_p=0.95,
            )

        with torch.no_grad():
            outputs = self.model.generate(**inputs, **gen_kwargs)

        decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
        
        # Usuwamy z response sam prompt, pobieramy to co dogenerował asystent.
        # Ponieważ skip_special_tokens=True usunęło <|im_start|>, splitujemy po czystym 'assistant' lub oryginalnym prompcie
        # Najprościej: usunąć oryginalny prompt z wyjścia
        clean_prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        # Hack dla pewności, bo skip_special_tokens modyfikuje wyjście
        try:
            input_length = inputs["input_ids"].shape[1]
            out_tokens = outputs[0][input_length:]
            response = self.tokenizer.decode(out_tokens, skip_special_tokens=True)
            return response.strip()
        except Exception:
            if "assistant\n" in decoded:
                return decoded.split("assistant\n")[-1].strip()
            elif "### Response:" in decoded:
                 return decoded.split("### Response:")[-1].strip()
        return decoded.strip()


    def analyze_file(self, file_path):
        filename = os.path.basename(file_path)
        print(f"\n🔎 Analizuję: \033[1m{filename}\033[0m")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception:
            print(f"⚠️  Pominięto (błąd odczytu): {filename}")
            return

        if not code.strip(): return

        token_count = self.count_tokens(code)
        if token_count > (self.context_window - 1500):
            print(f"⚠️  Pominięto: Zbyt duży plik ({token_count} tokenów).")
            return

        # 1. PROMPT DIAGNOSTYCZNY
        diag_prompt = f"""
        Jesteś ekspertem Code Review. Przeanalizuj poniższy kod.
        Wypisz TYLKO krytyczne błędy, luki bezpieczeństwa lub miejsca do optymalizacji.
        Jeśli kod jest idealny, napisz "OK".

        PLIK: {filename}
        KOD:
        {code[:2000]}
        """

        diagnosis = self.ask_brain(diag_prompt, max_new_tokens=256)

        if len(diagnosis) < 5 or "OK" in diagnosis.upper() and len(diagnosis) < 10:
            print("✅ Kod wygląda dobrze. Pomijam.")
            return

        print(f"🧠 Diagnoza AI:\n{diagnosis[:300]}...")

        action = input("\n[g] Generuj poprawkę / [s] Skip / [q] Wyjdź: ").lower()
        if action == 'q': sys.exit(0)
        if action == 's': return

        # 2. PROMPT NAPRAWCZY
        fix_prompt = f"""
        Jesteś Senior Developerem. Przepisz kod naprawiając znalezione problemy.
        Zastosuj zasady Clean Code i Type Hinting.
        Zwróć CAŁY poprawiony kod w bloku markdown.

        PLIK: {filename}
        KOD ORYGINALNY:
        {code}
        """

        print("🤖 Generuję kod...")
        raw_fix = self.ask_brain(fix_prompt, max_new_tokens=min(4096, token_count + 1000))
        new_code = self.extract_code_block(raw_fix)

        if not new_code:
            print("❌ AI nie zwróciło poprawnego bloku kodu.")
            return

        self.apply_changes(file_path, new_code)

    def apply_changes(self, file_path, new_code):
        print(f"\n--- PROPONOWANE ZMIANY ({os.path.basename(file_path)}) ---")
        lines = new_code.splitlines()
        print('\n'.join(lines[:15]))
        if len(lines) > 15: print(f"... (i {len(lines) - 15} więcej linii) ...")

        choice = input("\n💾 Zapisać zmiany? [y/n]: ").lower()
        if choice == 'y':
            shutil.copy(file_path, file_path + ".bak")  # Backup
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_code)
            print("✅ Zapisano.")
        else:
            print("❌ Anulowano.")

    def run(self):
        files = self.get_files()
        print(f"📂 Znaleziono {len(files)} plików do analizy.")

        for file_path in files:
            self.analyze_file(file_path)


if __name__ == "__main__":
    # Ścieżka do Twoich wytrenowanych adapterów
    ADAPTER_PATH = "moje_ai_adaptery"

    # Ścieżka do projektu, który chcesz analizować
    # UWAGA: Użyj r"" przed ścieżką
    PROJECT_PATH = r"C:\Users\mz100\PycharmProjects\ProjektTestowy"

    try:
        agent = SmartAgent(ADAPTER_PATH, PROJECT_PATH)
        agent.run()
    except KeyboardInterrupt:
        print("\n👋 Do widzenia.")
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"\n❌ Krytyczny błąd: {e}")
        input("Enter...")