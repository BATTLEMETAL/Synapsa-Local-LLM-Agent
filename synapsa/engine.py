"""
Synapsa — AI Engine (Production Grade)
Oparty na sprawdzonych wzorcach z:
- Audytor.py (model loading z BitsAndBytesConfig)
- Obserwator.py (LocalAIWorker._load_model)
- Launcher_Systemu.py (profil doboru modelu)
"""
import os
import sys
import json
import warnings
import logging

warnings.filterwarnings("ignore")
logging.getLogger("transformers").setLevel(logging.ERROR)

# Apply Windows compatibility fixes FIRST
try:
    from synapsa.compat import setup_windows_compatibility
    setup_windows_compatibility()
except Exception:
    pass


class SynapsaEngine:
    """
    Główny silnik AI.
    Inicjalizacja jest leniwa - model ładuje się dopiero przy pierwszym generate().
    To zapobiega crashom Streamlit przy starcie.
    """
    _instance = None  # Singleton pattern

    def __init__(self, adapter_path: str = None):
        self.model = None
        self.tokenizer = None
        self._adapter_path = adapter_path or os.getenv("ADAPTER_PATH", "moje_ai_adaptery")
        self._base_model = os.getenv("MODEL_PATH", "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit")
        self._max_new_tokens = int(os.getenv("MAX_SEQ_LENGTH", "2048"))
        self._loaded = False

    def _load_model(self):
        """Ładuje model - sprawdzony wzorzec z Audytor.py i Obserwator.py."""
        if self._loaded:
            return

        print("⏳ [SynapsaEngine] Ładowanie modelu AI...", flush=True)
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            from peft import PeftModel

            # 1. Określenie modelu bazowego (z configu adaptera lub .env)
            base_model = self._base_model
            adapter_config_path = os.path.join(self._adapter_path, "adapter_config.json")
            if os.path.exists(adapter_config_path):
                with open(adapter_config_path, "r") as f:
                    cfg = json.load(f)
                    base_model = cfg.get("base_model_name_or_path", base_model)

            print(f"   📦 Baza: {base_model}")

            # 2. BitsAndBytesConfig (sprawdzony wzorzec z Audytor.py)
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )

            # 3. Ładowanie modelu bazowego (sprawdzony wzorzec z Obserwator.py)
            self.model = AutoModelForCausalLM.from_pretrained(
                base_model,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=False,
            )

            # 4. Tokenizer
            tk_path = self._adapter_path if os.path.exists(self._adapter_path) else base_model
            self.tokenizer = AutoTokenizer.from_pretrained(tk_path, trust_remote_code=False)

            # 5. Adapter LoRA (jeśli istnieje)
            if os.path.exists(adapter_config_path):
                print("   🔗 Podłączam adaptery LoRA...")
                self.model = PeftModel.from_pretrained(self.model, self._adapter_path)

            self.model.eval()
            self._loaded = True
            print("✅ [SynapsaEngine] Model gotowy!", flush=True)

        except ImportError as e:
            import traceback
            traceback.print_exc()
            print(f"⚠️  [SynapsaEngine] Brak bibliotek ({e}). Przełączam na TRYB OFFLINE.")
            self._loaded = True  # Mark as loaded so we use fallback
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ [SynapsaEngine] Błąd ładowania: {e}")
            self._loaded = True  # Use fallback

    def generate(self, prompt: str, max_tokens: int = None) -> str:
        """
        Generuje odpowiedź.
        Jeśli model nie jest dostępny - używa trybu offline (deterministyczne odpowiedzi).
        """
        if not self._loaded:
            self._load_model()

        max_tokens = max_tokens or self._max_new_tokens

        # Jeśli model jest załadowany, używamy go
        if self.model and self.tokenizer:
            return self._generate_with_model(prompt, max_tokens)
        else:
            return self._generate_offline(prompt)

    def _generate_with_model(self, prompt: str, max_tokens: int) -> str:
        """Generuje z prawdziwym modelem - z Audytor.py generate_response()."""
        try:
            import torch
            # Prosty prompt wymuszający format odpowiedzi
            full_prompt = f"Instrukcja: Jesteś asystentem księgowym. Odpowiadaj zwięźle i poprawnym formatem.\n{prompt}\nOdpowiedź:"
            
            inputs = self.tokenizer([full_prompt], return_tensors="pt").to("cuda")
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    use_cache=True,
                    temperature=0.1,  # niska temperatura dla determinizmu
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
            
            # Pomiń tokeny promptu - szybsze i niezawodne
            input_length = inputs["input_ids"].shape[1]
            generated_tokens = outputs[0][input_length:]
            decoded = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
            
            # W razie gdyby model powtórzył prompt
            if "Odpowiedź:" in decoded:
                decoded = decoded.split("Odpowiedź:")[-1].strip()
                
            return decoded
        except Exception as e:
            return f"[Błąd generowania: {e}]"

    def generate_chat(self, system_message: str, user_message: str, max_tokens: int = None) -> str:
        """
        [MODERNIZACJA] Generuje odpowiedź w formacie ChatML — prawidłowy format dla Qwen 2.5+.
        Znacznie lepsze wyniki niż stały format Instruction/Response.
        """
        if not self._loaded:
            self._load_model()

        max_tokens = max_tokens or self._max_new_tokens

        if self.model and self.tokenizer:
            return self._generate_with_chatml(system_message, user_message, max_tokens)
        else:
            # Offline fallback — przekazujemy połączony prompt
            return self._generate_offline(f"{system_message}\n\n{user_message}")

    def _generate_with_chatml(self, system_message: str, user_message: str, max_tokens: int) -> str:
        """Generuje z prawdziwym modelem używając ChatML — natywny format Qwen 2.5."""
        try:
            import torch
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ]
            # apply_chat_template automatycznie buduje poprawny format <|im_start|>
            formatted = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            inputs = self.tokenizer([formatted], return_tensors="pt").to("cuda")
            input_length = inputs["input_ids"].shape[1]

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    use_cache=True,
                    temperature=0.2,
                    do_sample=True,
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
            # Dekoduj TYLKO nowe tokeny (nie powtarzaj promptu)
            generated_tokens = outputs[0][input_length:]
            return self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        except Exception as e:
            return f"[Błąd generowania ChatML: {e}]"

    def _generate_offline(self, prompt: str) -> str:
        """
        Tryb offline - deterministyczne odpowiedzi.
        Używany gdy model nie jest dostępny lub biblioteki nie są zainstalowane.
        """
        p = prompt.lower()
        # Dla audytu faktur
        if "faktura" in p or "vat" in p or "audit" in p or "audyt" in p:
            return json.dumps({
                "status": "DEMO_MODE",
                "raport": "TRYB DEMONSTRACYJNY (model AI niedostępny)\n\n"
                          "W trybie produkcyjnym AI sprawdzi:\n"
                          "- Kompletność danych (NIP, adres, data)\n"
                          "- Poprawność stawek VAT dla okresu faktury\n"
                          "- Zgodność z KSeF (od 2024)\n"
                          "- Mechanizm podzielonej płatności (>15000 PLN)\n\n"
                          "WNIOSEK: Plik oczekuje na analizę modelu AI.",
                "bledy_formalne": [],
                "rekomendacje": ["Uruchom model AI aby uzyskać pełny raport"]
            }, ensure_ascii=False, indent=2)
        # Dla kosztorysów budowlanych
        elif "kosztor" in p or "budow" in p or "cena" in p or "koszt" in p:
            return ("TRYB DEMONSTRACYJNY\n\n"
                    "Szacunkowe koszty dla typowych prac:\n"
                    "• Ocieplenie 1m²: 80-150 PLN (zależnie od grubości styropianu)\n"
                    "• Robocizna murarska: 40-80 PLN/m²\n"
                    "• Dachówka ceramiczna: 60-120 PLN/m²\n"
                    "• Tynk elewacyjny: 30-60 PLN/m²\n\n"
                    "Podaj szczegóły (metrage, materiał, region) dla dokładnej wyceny.")
        # Dla księgowej
        elif "styl" in p or "profil" in p or "nauczy" in p:
            return "Styl: Faktura z logo po lewej, data wystawienia u góry. Stawki VAT 23% i 8%. Dopisek 'Mechanizm podzielonej płatności' dla kwot >15000 PLN."
        elif "faktur" in p and ("wystaw" in p or "generu" in p):
            return ("FAKTURA VAT\n"
                    "─────────────────\n"
                    "Wystawca: [DANE WYSTAWCY]\n"
                    "Nabywca: [DANE NABYWCY]\n"
                    "Data wystawienia: [DATA]\n"
                    "Termin płatności: [DATA+14 dni]\n\n"
                    "LP | Opis | Ilość | Cena netto | VAT | Kwota brutto\n"
                    "1  | [USŁUGA/TOWAR] | 1 | [CENA] | 23% | [BRUTTO]\n\n"
                    "Razem netto: [SUMA]\n"
                    "Razem VAT: [VAT]\n"
                    "Razem brutto: [BRUTTO]\n\n"
                    "WNIOSEK: Uzupełnij danymi i wygeneruj PDF.")
        return "Synapsa AI — tryb demonstracyjny aktywny. Zainstaluj model AI dla pełnej funkcjonalności."

    @classmethod
    def get_instance(cls) -> "SynapsaEngine":
        """Singleton — jeden model w pamięci dla całej sesji."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
