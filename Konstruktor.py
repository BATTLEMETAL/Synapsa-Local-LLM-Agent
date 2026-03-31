import os
import json
import re
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


def setup_triton_mock():
    dummy_code = """
import sys
class UniversalMock:
    def __init__(self, name="Mock"): self._name = name
    def __getattr__(self, item): return self
    def __call__(self, *args, **kwargs): return self
    def __iter__(self): return iter([])
    def __getitem__(self, key): return self
    def __bool__(self): return False
sys.modules["triton"] = UniversalMock()
"""
    exec(dummy_code)


setup_triton_mock()


class ProjectConstructor:
    def __init__(self):
        print("🏗️  Inicjalizacja Konstruktora (Reasoning Edition)...")
        self._load_model()

    def _load_model(self):
        print("⏳ Ładowanie modelu...")
        base = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"
        bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16)

        try:
            self.model = AutoModelForCausalLM.from_pretrained(base, quantization_config=bnb, device_map="auto",
                                                              trust_remote_code=True)
            self.tokenizer = AutoTokenizer.from_pretrained(base, trust_remote_code=True)
            if os.path.exists(ADAPTER_PATH):
                print("🔗 Podłączono adaptery (Mózg Architekta).")
                self.model = PeftModel.from_pretrained(self.model, ADAPTER_PATH)
            self.model.eval()
        except Exception as e:
            print(f"❌ Błąd modelu: {e}")
            sys.exit(1)

    def generate(self, prompt, max_tokens=2048):
        # Formatowanie pod Qwen/Alpaca z wymuszeniem myślenia
        full_prompt = f"### Instruction:\n{prompt}\n\n### Response:\n<thinking>"

        inputs = self.tokenizer([full_prompt], return_tensors="pt").to("cuda")
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=max_tokens, temperature=0.2, do_sample=True)

        text = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

        # Wyciągamy odpowiedź po "### Response:"
        if "### Response:" in text:
            response = text.split("### Response:")[-1].strip()
        else:
            response = text.strip()

        # Dodajemy z powrotem tag otwierający <thinking>, bo prompt go "zjadł"
        if not response.startswith("<thinking>"):
            response = "<thinking>\n" + response

        return response

    def clean_output(self, text):
        """
        Kluczowa funkcja: Oddziela myśli od czystego kodu/JSONa.
        """
        thinking = ""
        content = text

        # Wyciągamy zawartość tagów <thinking>
        if "<thinking>" in text and "</thinking>" in text:
            parts = text.split("</thinking>")
            thinking = parts[0].replace("<thinking>", "").strip()
            content = parts[1].strip()

        # Dodatkowe czyszczenie Markdowna dla kodu
        match = re.search(r"```(?:\w+)?\n(.*?)```", content, re.DOTALL)
        if match:
            content = match.group(1).strip()

        return thinking, content

    def extract_json(self, text):
        _, content = self.clean_output(text)
        try:
            # Próba znalezienia JSONa w czystej treści
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                return json.loads(content[start:end + 1])
        except:
            pass
        return None

    def create_architecture(self, description):
        print(f"\n📐 Projektuję architekturę...")

        prompt = f"""
        You are a Principal Software Architect.
        Create a file structure for a Python project described as: "{description}".

        Think carefully about the architecture patterns (MVC, Clean Architecture, etc.) inside <thinking> tags.

        Then return a JSON object:
        {{
          "files": [
            {{"path": "main.py", "description": "Entry point"}},
            {{"path": "core/engine.py", "description": "Business logic"}}
          ]
        }}
        """

        response = self.generate(prompt)
        thinking, plan_json = self.clean_output(response)

        print(f"🧠 Myśli Architekta:\n{thinking[:500]}...\n")

        plan = self.extract_json(response)
        if not plan:
            print("⚠️ Nie udało się sparsować JSONa. Próbuję jeszcze raz...")
            return self.create_architecture(description)  # Retry recursion

        return plan

    def build(self, project_name, description):
        # 1. Planowanie
        plan = self.create_architecture(description)
        if not plan: return

        print("\n📋 ZATWIERDZONY PLAN:")
        for f in plan['files']:
            print(f"  - {f['path']}")

        if input("\nBudować? [y/n]: ").lower() != 'y': return

        # 2. Katalogi
        root = os.path.join(os.path.dirname(os.getcwd()), project_name)
        os.makedirs(root, exist_ok=True)

        structure_context = "\n".join([f"- {x['path']}: {x['description']}" for x in plan['files']])

        # 3. Generowanie (z myśleniem)
        for item in plan['files']:
            full_path = os.path.join(root, item['path'])
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            print(f"🔨 Koduję: {item['path']}...")

            prompt = f"""
            You are a Senior Python Developer. Write code for: '{item['path']}'.

            PROJECT CONTEXT: {description}
            FULL STRUCTURE:
            {structure_context}

            TASK:
            1. Analyze dependencies inside <thinking>.
            2. Write the complete, production-ready code.
            """

            response = self.generate(prompt, max_tokens=3000)  # Więcej tokenów na kod
            thinking, code = self.clean_output(response)

            # Zapisujemy tylko KOD (bez myśli)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code)

            print(f"   ✅ Zapisano. (Architekt przemyślał to w {len(thinking)} znakach)")

        print(f"\n🎉 Projekt '{project_name}' gotowy w folderze: {root}")


if __name__ == "__main__":
    builder = ProjectConstructor()
    name = input("\nNazwa folderu projektu: ")
    desc = input("Opis projektu: ")
    if name and desc:
        builder.build(name, desc)