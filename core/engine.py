import os
import sys

# Pancerna kompatybilność przeniesiona do jednego wspólnego miejsca
try:
    from synapsa.compat import setup_windows_compatibility
    setup_windows_compatibility()
except ImportError:
    pass

import torch
import warnings
import re
from config import settings

warnings.filterwarnings("ignore")

class SynapsaEngine:
    """
    Zunifikowany silnik AI Synapsy.
    Obsługuje leniwe ładowanie modelu (lazy loading), adapterów LoRA i inteligentną ekstrakcję kodu.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SynapsaEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_path = settings.BASE_MODEL
        self.adapter_path = getattr(settings, "ADAPTERS", os.getenv("ADAPTER_PATH", "moje_ai_adaptery"))
        
        self.model = None
        self.tokenizer = None
        self._initialized = True
        print("⏳ [core.engine] Zainicjalizowano podwójny interfejs AI. Model wczyta się leniwie przy pierwszej potrzebie (Lazy Load).")

    def _load_model(self):
        """Metoda ładująca ciężki model VRAM dopiero przed faktycznym wygenerowaniem pierwszej odpowiedzi."""
        if self.model is not None:
            return
            
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel

        print(f"⏳ Pobieranie bloków pamięci dla modelu: {self.model_path} (Tryb 4-bit NF4)...")

        try:
            # Konfiguracja BitsAndBytes (zoptymalizowana pod RTX 3060 - 12GB)
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )

            # Ładowanie tokenizera
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )

            # Ładowanie modelu bazowego (Zajmuje zasoby GPU)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True
            )

            # Podłączanie Twoich adapterów LoRA (jeśli istnieją)
            if os.path.exists(self.adapter_path):
                print(f"🔗 Podłączanie adapterów wiedzy eksperckiej z: {self.adapter_path}")
                self.model = PeftModel.from_pretrained(self.model, self.adapter_path)

            self.model.eval()
            print(f"✅ Silnik docelowy Synapsy jest gotowy na akceleratorze: {torch.cuda.get_device_name(0)}")

        except Exception as e:
            print(f"❌ KRYTYCZNY BŁĄD SILNIKA: {e}")
            sys.exit(1)

    def generate_raw(self, prompt, max_tokens=2048, temperature=0.2):
        """Generuje surową odpowiedź z modelu po upewnieniu się, że siedzi w pamięci."""
        # Odpalamy leniwe ładowanie przed każdą robotą. Będzie szybkie jak błyskawica jeśli moduł wczytało już wcześniej.
        self._load_model()
        
        formatted_prompt = f"### Instruction:\n{prompt}\n\n### Response:\n"

        # Opcjonalne wymuszenie myślenia (Reasoning Mode z pliku Konstruktor.py)
        if "Think carefully" in prompt or "Analyze" in prompt:
            formatted_prompt += "<thinking>\n"

        inputs = self.tokenizer([formatted_prompt], return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                repetition_penalty=1.1,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )

        decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

        # Wyciągamy to co po Response:
        if "### Response:" in decoded:
            response = decoded.split("### Response:")[-1].strip()
        else:
            response = decoded.strip()

        # Jeśli wymusiliśmy <thinking>, a model go nie dodał w decode, naprawiamy to
        if formatted_prompt.endswith("<thinking>\n") and not response.startswith("<thinking>"):
            response = "<thinking>\n" + response

        return response

    def clean_output(self, text):
        """
        Oddziela myśli (<thinking>) od czystego kodu.
        Logika z pliku Konstruktor.py
        """
        thinking = ""
        content = text

        if "<thinking>" in text and "</thinking>" in text:
            parts = text.split("</thinking>")
            thinking = parts[0].replace("<thinking>", "").strip()
            content = parts[1].strip()
        elif "<thinking>" in text:
            # Jeśli model nie zamknął tagu
            parts = text.split("<thinking>")
            content = parts[-1].strip()

        # Ekstrakcja kodu z Markdown (logika z Audytor.py)
        code_match = re.search(r"```(?:\w+)?\n(.*?)```", content, re.DOTALL)
        if code_match:
            content = code_match.group(1).strip()

        return thinking, content

    def generate_chat(self, system_message: str, user_message: str, max_tokens: int = 2048) -> str:
        """
        [MODERNIZACJA] ChatML format dla Qwen 2.5+.
        Używaj tego zamiast generate_raw() / smart_generate() dla zadań agentów (audyt, faktury).
        """
        self._load_model()
        if self.model is None or self.tokenizer is None:
            return self._offline_fallback(f"{system_message}\n{user_message}")

        try:
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ]
            formatted = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.tokenizer([formatted], return_tensors="pt").to(self.device)
            input_length = inputs["input_ids"].shape[1]

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=0.2,
                    do_sample=True,
                    repetition_penalty=1.1,
                    top_p=0.95,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
            generated_tokens = outputs[0][input_length:]
            return self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        except Exception as e:
            return f"[Błąd generate_chat: {e}]"

    def _offline_fallback(self, prompt: str) -> str:
        return "[TRYB OFFLINE] Model AI niedostępny. Uruchom aplikację z dostępną kartą graficzną."

    def smart_generate(self, prompt, max_tokens=2048):
        """Pełny proces: Generowanie -> Czyszczenie -> Wynik"""
        raw = self.generate_raw(prompt, max_tokens)
        thinking, code = self.clean_output(raw)

        if thinking:
            print(f"\n🧠 MYŚLI AI: {thinking[:150]}...")

        return code