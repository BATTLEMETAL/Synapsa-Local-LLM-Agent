"""
Synapsa — AccountantAgent (Wirtualna Księgowa)
Wzorowana na wzorcach z Nauczyciel.py (analiza plików + JSON output)
i Obserwator.py (przetwarzanie bez modyfikacji oryginałów).
"""
import os
import json
import shutil
import uuid
import logging

logger = logging.getLogger(__name__)


class AccountantAgent:
    """
    Wirtualna Księgowa:
    1. Uczy się stylu z przykładowych faktur (KOPIA — oryginały bezpieczne)
    2. Generuje nowe faktury w danym stylu
    """

    SAFE_ZONE = "synapsa_workspace/accountant_safe_zone"
    KNOWLEDGE_FILE = "synapsa_workspace/accountant_knowledge.json"

    def __init__(self, engine=None):
        if engine is None:
            from synapsa.engine import SynapsaEngine
            self.engine = SynapsaEngine.get_instance()
        else:
            self.engine = engine

        self.style = self._load_knowledge()

    def _load_knowledge(self) -> dict:
        """Ładuje zapisaną wiedzę o stylu fakturowania."""
        if os.path.exists(self.KNOWLEDGE_FILE):
            try:
                with open(self.KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"rules": "", "templates": [], "session_count": 0}

    def _save_knowledge(self):
        """Zapisuje wiedzę do pliku."""
        os.makedirs(os.path.dirname(self.KNOWLEDGE_FILE), exist_ok=True)
        with open(self.KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.style, f, indent=4, ensure_ascii=False)

    def _isolate_files(self, file_paths: list) -> list:
        """
        BEZPIECZEŃSTWO: Kopiuje pliki do bezpiecznej strefy.
        Wzorzec z Obserwator.py — oryginały NIE są modyfikowane.
        """
        session_id = str(uuid.uuid4())[:8]
        safe_dir = os.path.join(self.SAFE_ZONE, f"session_{session_id}")
        os.makedirs(safe_dir, exist_ok=True)

        isolated = []
        for path in file_paths:
            if os.path.exists(path):
                dest = os.path.join(safe_dir, os.path.basename(path))
                shutil.copy2(path, dest)
                isolated.append(dest)
                logger.debug(f"Izolowano: {os.path.basename(path)} -> {dest}")

        return isolated

    def learn_from_examples(self, file_paths: list) -> str:
        """
        Analizuje przykładowe faktury i uczy się stylu.
        Wzorowane na Teacher.process_file() z Nauczyciel.py.
        """
        print(f"👩‍💼 [Accountant] Analizuję {len(file_paths)} wzór(ów) faktur...", flush=True)

        # IZOLACJA: zawsze pracujemy na kopiach
        isolated = self._isolate_files(file_paths)

        file_names = ", ".join([os.path.basename(f) for f in isolated])
        num_files = len(isolated)

        prompt = f"""Jesteś Asystentem Księgowym AI.
Użytkownik przesłał {num_files} przykładowych faktur (pliki: {file_names}).

ZADANIE:
Stwórz "Profil Stylu" wystawiania faktur na podstawie tych przykładów.
Opisz:
1. Układ dokumentu (logo po lewej/prawej, dane u góry/dole)
2. Stosowane stawki VAT (np. 23%, 8%)
3. Sposób opisu usług (szczegółowy/skrótowy)
4. Specjalne dpiski (MPP, przedpłata, itp.)
5. Format dat i numerów

FORMAT: Krótki opis stylu w 3-5 zdaniach, gotowy do użycia przy generowaniu.
Np.: "Styl: Logo po lewej, data wystawienia u góry prawej. Stawki 23% i 8%..."
"""
        analysis = self.engine.generate(prompt, max_tokens=500)

        # Zapisz wiedzę
        self.style["rules"] = analysis
        self.style["session_count"] = self.style.get("session_count", 0) + 1
        self.style["templates"].append(f"Sesja #{self.style['session_count']}: {file_names}")
        self._save_knowledge()

        return f"✅ Nauczyłam się nowego stylu!\n\nWnioski:\n{analysis}"

    def generate_invoice(self, invoice_data: str) -> str:
        """
        Generuje fakturę na podstawie podanych danych i zapamiętanego stylu.
        """
        style_context = self.style.get("rules", "Standardowy styl polskiej faktury VAT.")

        prompt = f"""Jesteś Asystentem Księgowym. Wystawiasz faktury VAT.

ZAPAMIĘTANY STYL:
{style_context}

DANE DO FAKTURY:
{invoice_data}

ZADANIE:
Wygeneruj kompletną fakturę VAT w tekstowym formacie.
Uwzględnij: numer faktury, datę, dane sprzedawcy i nabywcy, pozycje, kwoty netto/VAT/brutto.
Jeśli kwota przekracza 15000 PLN — dodaj dopisek "Mechanizm podzielonej płatności".
"""
        return self.engine.generate(prompt, max_tokens=1500)
