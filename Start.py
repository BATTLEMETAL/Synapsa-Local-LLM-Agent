import os
import sys
import warnings
import importlib.util
import importlib.metadata
import unittest.mock

# ==============================================================================
# 1. SYSTEM PATCHER (NAPRAWA WINDOWSA)
# ==============================================================================
print("\033[95m🛡️  Inicjalizacja (Windows Native + New Transformers)...\033[0m")
warnings.filterwarnings("ignore")

# --- FIX 1: TRITON (Blokada całkowita) ---
os.environ["WBITS_USE_TRITON"] = "0"
os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"

# Przechwytujemy każde żądanie o Tritona i zwracamy None
_orig_find_spec = importlib.util.find_spec


def _patched_find_spec(name, package=None):
    if name == "triton" or name.startswith("triton."):
        return None
    return _orig_find_spec(name, package)


importlib.util.find_spec = _patched_find_spec

# --- FIX 2: BITSANDBYTES (Obsługa 4-bit na Windows) ---
try:
    import bitsandbytes as bnb

    # 1. Oszukujemy system, że mamy wersję wspierającą NF4
    bnb.__version__ = "0.43.3"

    if not hasattr(importlib.metadata, "_original_version"):
        importlib.metadata._original_version = importlib.metadata.version


    def _patched_version(dist_name):
        if dist_name == "bitsandbytes": return "0.43.3"
        return importlib.metadata._original_version(dist_name)


    importlib.metadata.version = _patched_version

    # 2. Uzupełniamy braki w starej bibliotece
    if not hasattr(bnb.utils, "pack_dict_to_tensor"):
        bnb.utils.pack_dict_to_tensor = lambda *args, **kwargs: None
    if not hasattr(bnb.utils, "unpack_tensor_to_dict"):
        bnb.utils.unpack_tensor_to_dict = lambda *args, **kwargs: {}

    # 3. Naprawiamy klasę Params4bit (metody .to i from_prequantized)
    from bitsandbytes.nn import Params4bit

    if not hasattr(Params4bit, "from_prequantized"):
        def from_prequantized(cls, *args, **kwargs):
            data = kwargs.get('data') or args[0]
            return cls(data=data, requires_grad=False)


        Params4bit.from_prequantized = classmethod(from_prequantized)

    import torch


    def safe_to(self, *args, **kwargs):
        return super(torch.nn.Parameter, self).to(*args, **kwargs)


    Params4bit.to = safe_to

except ImportError:
    print("⚠️ Błąd: Nie znaleziono bitsandbytes.")

# --- FIX 3: COMPILER (Blokada torch.compile) ---
import torch

torch.compile = lambda *args, **kwargs: (lambda x: x)

# ==============================================================================
# 2. LOGIKA AUDYTORA
# ==============================================================================
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TextStreamer
from peft import PeftModel

ADAPTER_PATH = "moje_ai_adaptery"
BASE_MODEL = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"


class CodeAuditor:
    def __init__(self):
        if not os.path.exists(ADAPTER_PATH):
            print(f"❌ Brak folderu: {ADAPTER_PATH}");
            sys.exit(1)

        print("⚙️  Konfiguracja NF4 (Nowy Standard)...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )

        try:
            print(f"⏳ Ładowanie modelu bazowego: {BASE_MODEL}")
            self.base_model = AutoModelForCausalLM.from_pretrained(
                BASE_MODEL,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True
            )
            self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

            print("🔗 Podpinanie adapterów (PEFT)...")
            self.model = PeftModel.from_pretrained(self.base_model, ADAPTER_PATH)
            self.model.eval()
            print("\033[92m✅ GOTOWE! Audytor uruchomiony.\033[0m")

        except Exception as e:
            print(f"\n❌ Błąd ładowania: {e}")
            sys.exit(1)

    def generate(self, prompt):
        inputs = self.tokenizer([prompt], return_tensors="pt").to("cuda")
        streamer = TextStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)

        print("\n\033[96m🤖 Generowanie...\033[0m")
        with torch.no_grad():
            self.model.generate(
                **inputs,
                streamer=streamer,
                max_new_tokens=1024,
                temperature=0.2,
                do_sample=True
            )

    def run(self):
        while True:
            path = input("\n📂 Podaj plik (q=wyjście): ").strip('"')
            if path.lower() == 'q': break

            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    prompt = f"Sprawdź ten kod i popraw błędy:\n\n{code[:3000]}"
                    self.generate(prompt)
                except Exception as e:
                    print(f"Błąd pliku: {e}")
            else:
                print("❌ Brak pliku.")


if __name__ == "__main__":
    CodeAuditor().run()