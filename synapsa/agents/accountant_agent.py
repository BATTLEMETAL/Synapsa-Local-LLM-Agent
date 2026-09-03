"""
Synapsa — AccountantAgent (Wirtualna Księgowa)
Wzorowana na wzorcach z Nauczyciel.py (analiza plików + JSON output)
i Obserwator.py (przetwarzanie bez modyfikacji oryginałów).
"""
import os
import re
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

    def _extract_files_content(self, files: list) -> str:
        """
        [FIX] Czyta rzeczywistą treść każdego pliku.
        Obsługuje PDF/obrazy przez PyMuPDF, TXT bezpośrednio.
        Skopiowany wzorzec z SecureAuditAgent._extract_files_content().
        """
        all_text = []
        for path in files:
            filename = os.path.basename(path)
            content = self._read_file_content(path)
            if content.strip():
                truncated = content[:4000]
                if len(content) > 4000:
                    truncated += "\n[... skrócono do 4000 znaków ...]"
                all_text.append(f"=== PLIK: {filename} ===\n{truncated}")
            else:
                all_text.append(f"=== PLIK: {filename} === [nie udało się odczytać treści]")
        return "\n\n".join(all_text)

    def _read_file_content(self, path: str) -> str:
        """Czyta treść pliku — PDF/obraz przez PyMuPDF, reszta jako tekst."""
        ext = os.path.splitext(path)[1].lower()

        # PDF i obrazy
        if ext in (".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"):
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(path)
                pages = []
                for page in doc:
                    text = page.get_text("text")
                    if len(text.strip()) > 20:
                        pages.append(text)
                    else:
                        try:
                            words = page.get_text("words")
                            pages.append(" ".join([w[4] for w in words]))
                        except Exception:
                            pages.append(text)
                doc.close()
                result = "\n".join(pages).strip()
                if result:
                    return result
            except ImportError:
                logger.warning("PyMuPDF nie jest zainstalowane — pip install pymupdf")
            except Exception as e:
                logger.warning(f"PyMuPDF błąd dla {path}: {e}")

        # Pliki tekstowe
        if ext in (".txt", ".csv"):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception:
                pass

        # Excel
        if ext in (".xlsx", ".xls"):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
                lines = []
                for ws in wb.worksheets:
                    for row in ws.iter_rows(values_only=True):
                        row_text = "\t".join(str(c) for c in row if c is not None)
                        if row_text.strip():
                            lines.append(row_text)
                return "\n".join(lines)
            except Exception:
                pass

        return ""

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

        # [FIX] Czytamy RZECZYWISTĄ treść plików — wcześniej prompt miał tylko nazwy
        files_content = self._extract_files_content(isolated)

        system_msg = (
            "Jesteś Asystentem Księgowym AI. "
            "Analizujesz przykładowe faktury i tworzysz profil stylu wystawiania dokumentów. "
            "Odpowiadasz konkretnie i zwięźle po polsku."
        )

        user_msg = f"""Użytkownik przesłał {num_files} przykładowych faktur (pliki: {file_names}).

TREŚĆ FAKTUR:
{files_content}

ZADANIE:
Na podstawie powyższej treści stwórz "Profil Stylu" wystawiania faktur.
Opisz:
1. Układ dokumentu (logo po lewej/prawej, dane u góry/dole)
2. Stosowane stawki VAT (np. 23%, 8%)
3. Sposób opisu usług (szczegółowy/skrótowy)
4. Specjalne dopiski (MPP, przedpłata, itp.)
5. Format dat i numerów faktury

FORMAT: Krótki opis stylu w 3-5 zdaniach.
Np.: "Styl: Logo po lewej, data wystawienia u góry prawej. Stawki 23% i 8%..."
"""
        analysis = self.engine.generate_chat(system_msg, user_msg, max_tokens=500)

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
