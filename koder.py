import os
import sys
import torch
import warnings
import importlib.util
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TextStreamer
from peft import PeftModel

# ==========================================
# 1. KONFIGURACJA SYSTEMOWA (Windows Fixes)
# ==========================================
os.environ["WBITS_USE_TRITON"] = "0"
os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"
os.environ["TORCH_CUDA_ARCH_LIST"] = "8.6"  # Ustawienie pod RTX 30xx
warnings.filterwarnings("ignore")


# ==========================================
# 2. PANCERNY MOCK TRITONA (Stabilność)
# ==========================================
def setup_triton_mock():
    """
    Tworzy atrapę Tritona, która nie powoduje crashy na Windows.
    Jest to ta sama wersja, która działa w Audytor_Ultimate.py.
    """
    dummy_code = '''
class UniversalMock:
    def __init__(self, name="Mock"): self._name = name
    def __getattr__(self, item): return self
    def __call__(self, *args, **kwargs): return self
    def __iter__(self): return iter([]) # Kluczowe dla pętli for x in triton...
    def __getitem__(self, key): return self
    def __bool__(self): return False
    def __int__(self): return 1
    def __float__(self): return 1.0

import sys
mock = UniversalMock()
# Rejestrujemy atrapę wszędzie gdzie się da
sys.modules["triton"] = mock
sys.modules["triton.language"] = mock
sys.modules["triton.compiler"] = mock
'''
    dummy_name = "triton_dummy_koder.py"
    with open(dummy_name, "w", encoding="utf-8") as f: f.write(dummy_code)
    spec = importlib.util.spec_from_file_location("triton", dummy_name)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["triton"] = module
        spec.loader.exec_module(module)


setup_triton_mock()

# ==========================================
# 3. KONFIGURACJA MODELU
# ==========================================
ADAPTER_PATH = "moje_ai_adaptery"  # Folder z Twoim treningiem
BASE_MODEL = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"


def main():
    print("─" * 50)
    print("🧠 SYNAPSA SENIOR | KODER INTERACTIVE (Windows Safe)")
    print("─" * 50)

    try:
        print("⏳ Ładowanie modelu bazowego (4-bit)...")

        # Konfiguracja kwantyzacji (zgodna z Twoim trenerem)
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

        # Ładowanie bazy
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )

        # Ładowanie tokenizera
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)

        # Ładowanie Twojego mózgu (Adaptery LoRA)
        if os.path.exists(ADAPTER_PATH):
            print(f"🔗 Podłączanie adapterów z: {ADAPTER_PATH}")
            model = PeftModel.from_pretrained(model, ADAPTER_PATH)
        else:
            print("⚠️ Nie znaleziono adapterów. Uruchamiam czysty model bazowy.")

        model.eval()
        print("\n✅ SYSTEM GOTOWY. Czekam na polecenia.")

    except Exception as e:
        print(f"\n❌ KRYTYCZNY BŁĄD PODCZAS STARTU:\n{e}")
        input("Naciśnij Enter, aby zamknąć...")
        return

    # ==========================================
    # 4. PĘTLA ROZMOWY
    # ==========================================
    streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    while True:
        try:
            query = input("\n💻 (Koder) >>> ")
            if query.lower() in ['q', 'exit', 'wyjdz']:
                break
            if not query.strip():
                continue

            # Wymuszamy tryb myślenia (Reasoning), jeśli model był tak trenowany
            # Format Qwen/Alpaca
            prompt = f"### Instruction:\nJesteś Senior Software Architektem. {query}\n\n### Response:\n<thinking>"

            inputs = tokenizer([prompt], return_tensors="pt").to("cuda")

            print("\n" + "─" * 40)
            # Wypisujemy początek tagu, bo streamer go pominie (skip_prompt=True ucina prompt)
            print("<thinking>", end="", flush=True)

            with torch.no_grad():
                model.generate(
                    **inputs,
                    streamer=streamer,
                    max_new_tokens=2048,
                    temperature=0.2,  # Niska temperatura dla precyzji w kodzie
                    do_sample=True,
                    repetition_penalty=1.1
                )
            print("\n" + "─" * 40)

        except KeyboardInterrupt:
            print("\n🛑 Przerwano generowanie.")
            continue
        except Exception as e:
            print(f"❌ Błąd generowania: {e}")


if __name__ == "__main__":
    main()