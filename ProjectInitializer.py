import os
import sys
import torch
import warnings
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# ==========================================
# KONFIGURACJA
# ==========================================
ADAPTER_PATH = "moje_ai_adaptery"
os.environ["WBITS_USE_TRITON"] = "0"
os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"
os.environ["TORCH_CUDA_ARCH_LIST"] = "8.6"
warnings.filterwarnings("ignore")


# --- PANCERNY MOCK TRITONA ---
def setup_triton_mock():
    """Tworzy atrapę Tritona, która nie wysypuje się przy iteracji."""
    import sys

    # Definicja klasy Mock, która udaje wszystko
    dummy_code = """
import sys
class UniversalMock:
    def __init__(self, name="Mock"): self._name = name

    # Udajemy dowolny atrybut/metodę
    def __getattr__(self, item): return self

    # Udajemy funkcję
    def __call__(self, *args, **kwargs): return self

    # Udajemy listę/iterator (KLUCZOWA POPRAWKA DLA BŁĘDU ITERABLE)
    def __iter__(self): return iter([])

    # Udajemy słownik/listę przy dostępie indeksowym
    def __getitem__(self, key): return self

    # Udajemy False w warunkach logicznych (żeby nie wchodzić w if triton:)
    def __bool__(self): return False

# Rejestrujemy atrapę w systemie pod różnymi nazwami, których szuka bitsandbytes
mock_instance = UniversalMock()
sys.modules["triton"] = mock_instance
sys.modules["triton.language"] = mock_instance
sys.modules["triton.compiler"] = mock_instance
"""
    exec(dummy_code)


setup_triton_mock()


class ProjectInitiator:
    def __init__(self):
        print("🧠 Inicjalizacja Synapsy (Tryb Analityka Biznesowego)...")
        self._load_model()
        self.conversation_history = ""

    def _load_model(self):
        print("⏳ Ładowanie wag i adapterów...")
        base = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"
        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )

        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                base,
                quantization_config=bnb,
                device_map="auto",
                trust_remote_code=True
            )
            self.tokenizer = AutoTokenizer.from_pretrained(base, trust_remote_code=True)

            if os.path.exists(ADAPTER_PATH):
                print(f"🔗 Podłączanie adapterów z: {ADAPTER_PATH}")
                self.model = PeftModel.from_pretrained(self.model, ADAPTER_PATH)

            self.model.eval()
            print("✅ Model załadowany.")

        except Exception as e:
            print(f"❌ Błąd ładowania modelu: {e}")
            sys.exit(1)

    def ask_brain(self, prompt):
        inputs = self.tokenizer([prompt], return_tensors="pt").to("cuda")
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs, max_new_tokens=1024, temperature=0.3, do_sample=True, repetition_penalty=1.1
            )

        text = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
        if "### Response:" in text: return text.split("### Response:")[-1].strip()
        return text.strip()

    def analyze_requirements(self, initial_idea):
        print("\n🤔 Analizuję Twoje wymagania...")

        prompt = f"""### Instruction:
You are a Senior Solutions Architect.
User wants to build: "{initial_idea}".

Analyze this request. Do you have enough information to build a robust, professional system?
If NO, list 3-4 critical questions to the user about data sources, formats, or tech stack.
If YES, write "READY".

### Response:
"""
        response = self.ask_brain(prompt)

        if "READY" not in response and "?" in response:
            print(f"\n✋ Synapsa potrzebuje doprecyzowania:\n{response}")
            print("\n💡 Odpowiedz na te pytania (lub wciśnij Enter, by pominąć):")
            user_details = input(">>> ")

            if user_details.strip():
                return f"{initial_idea}. User details: {user_details}"

        return initial_idea

    def generate_tech_spec(self, requirements):
        print("\n📐 Opracowuję Specyfikację Techniczną...")

        prompt = f"""### Instruction:
Create a Technical Specification for a Python project based on: "{requirements}".
Decide on the best libraries based on performance and clean code.

Output format:
1. Project Name
2. Tech Stack (Libraries)
3. Architecture (Modules and their responsibility)
4. List of files to create

### Response:
"""
        spec = self.ask_brain(prompt)
        print(f"\n📋 PROJEKT:\n{spec}")
        return spec

    def build_structure(self, spec):
        print("\n🏗️  Generuję strukturę plików na podstawie specyfikacji...")

        prompt = f"""### Instruction:
Based on this spec:
{spec}

Generate a JSON list of files to create.
Format: {{"files": [{{"path": "main.py", "description": "..."}}]}}

### Response:
```json
"""
        response = self.ask_brain(prompt)
        print("\n✅ PLAN BUDOWY GOTOWY.")
        print(
            "Aby go zrealizować, uruchom skrypt 'Konstruktor.py' i wklej mu ten plan (lub po prostu nazwę i opis projektu).")
        print("-" * 30)
        print(response)
        print("-" * 30)


if __name__ == "__main__":
    try:
        bot = ProjectInitiator()

        print("\n--- SYNAPSA ARCHITECT ---")
        idea = input("Co chcesz zbudować? ")

        if idea:
            refined_idea = bot.analyze_requirements(idea)
            spec = bot.generate_tech_spec(refined_idea)

            if input("\nCzy budować ten system? [y/n]: ").lower() == 'y':
                bot.build_structure(spec)
    except KeyboardInterrupt:
        print("\n👋 Przerwano.")
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"\n❌ Błąd krytyczny: {e}")