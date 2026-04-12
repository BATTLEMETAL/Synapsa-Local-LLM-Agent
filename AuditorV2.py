import os
import sys
import torch
import warnings
import time
import json
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# ==========================================
# KONFIGURACJA LOKALNA (PRODUKTOWA)
# ==========================================
ADAPTER_PATH = "moje_ai_adaptery"  # Twój wytrenowany mózg
os.environ["WBITS_USE_TRITON"] = "0"
os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"
os.environ["TORCH_CUDA_ARCH_LIST"] = "8.6"
warnings.filterwarnings("ignore")


# --- PANCERNY MOCK TRITONA (TO NAPRAWIA BŁĄD) ---
def setup_triton_mock():
    dummy_code = """
import sys
class UniversalMock:
    def __init__(self, name="Mock"): self._name = name
    def __getattr__(self, item): return self
    def __call__(self, *args, **kwargs): return self
    def __iter__(self): return iter([]) # <--- KLUCZOWA POPRAWKA
    def __getitem__(self, key): return self
    def __bool__(self): return False

mock_instance = UniversalMock()
sys.modules["triton"] = mock_instance
sys.modules["triton.language"] = mock_instance
sys.modules["triton.compiler"] = mock_instance
"""
    exec(dummy_code)


setup_triton_mock()

# ==========================================
# SCENARIUSZE TESTOWE (REAL WORLD)
# ==========================================
TESTS = [
    {
        "name": "1. Integracja API (Weather)",
        "prompt": """
        Write a Python script to fetch current weather for a given city using 'requests'.
        API URL: https://api.weather.com/v1/current?city={city}
        Requirements:
        - Handle timeouts and 404 errors.
        - Parse JSON response safely.
        - Print "Temperature: X" or "Error: Y".
        - Use Type Hinting.
        """
    },
    {
        "name": "2. Analiza Logów (Regex)",
        "prompt": """
        Write a function `parse_logs(log_text)` that extracts all IP addresses and error codes (4xx/5xx) from a server log string.
        Log format: "2024-01-01 12:00 [IP: 192.168.1.1] GET /index.html 200"
        Use Python `re` module. Return a dictionary: {"ips": [...], "errors": [...]}.
        """
    },
    {
        "name": "3. Generator PDF (ReportLab)",
        "prompt": """
        Write a Python function `create_invoice(filename, items)` using 'reportlab'.
        'items' is a list of dicts: {'name': str, 'price': float}.
        The PDF should have:
        - A title "INVOICE".
        - A list of items with prices.
        - A total sum at the bottom.
        """
    }
]


class ProductDemo:
    def __init__(self):
        print("\n💼 INICJALIZACJA DEMO PRODUKTU (SYNAPSA PYTHON)...")
        self._load_model()

    def _load_model(self):
        print("⏳ Ładowanie Twojego silnika AI...")
        base = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"
        bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16)

        try:
            self.model = AutoModelForCausalLM.from_pretrained(base, quantization_config=bnb, device_map="auto",
                                                              trust_remote_code=True)
            self.tokenizer = AutoTokenizer.from_pretrained(ADAPTER_PATH, trust_remote_code=True)
            self.model = PeftModel.from_pretrained(self.model, ADAPTER_PATH)
            self.model.eval()
            print("✅ Silnik gotowy.\n")
        except Exception as e:
            print(f"❌ Błąd modelu: {e}")
            sys.exit(1)

    def run_demo(self):
        results = []
        for test in TESTS:
            print(f"🎬 Scena: {test['name']}...")
            start = time.time()

            prompt = f"### Instruction:\n{test['prompt']}\n\n### Response:\n"
            inputs = self.tokenizer([prompt], return_tensors="pt").to("cuda")

            with torch.no_grad():
                out = self.model.generate(**inputs, max_new_tokens=1024, temperature=0.1, do_sample=True)

            # Dekodowanie i czyszczenie
            full_text = self.tokenizer.decode(out[0], skip_special_tokens=True)
            if "### Response:" in full_text:
                response = full_text.split("### Response:")[-1].strip()
            else:
                response = full_text.strip()

            duration = time.time() - start

            print(f"   ⏱️ Czas reakcji: {duration:.2f}s")
            results.append(f"# {test['name']}\n```python\n{response}\n```\n")

        filename = "DEMO_RESULT.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(results))
        print(f"\n📄 Wyniki zapisano w {filename}. Sprawdź je!")


if __name__ == "__main__":
    ProductDemo().run_demo()