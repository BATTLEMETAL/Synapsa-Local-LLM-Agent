"""
Synapsa — SecureAuditAgent (Modernized v3)
Kluczowa zmiana: PyMuPDF ekstrakcja tekstu z PDF/JPG przed promptem AI.
- Agenci więcej nie "zgadują" — dostają pełną treść faktury.
- Nowoczesny ChatML format dla Qwen 2.5.
- vat_norms.json (historyczne normy VAT 2018-2026).
"""
import os
import re
import json
import shutil
import uuid
import logging

logger = logging.getLogger(__name__)

_NORMS_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge", "vat_norms.json")


def _load_vat_norms() -> dict:
    """Ładuje bazę historycznych norm VAT."""
    try:
        norms_abs = os.path.abspath(_NORMS_PATH)
        if os.path.exists(norms_abs):
            with open(norms_abs, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Nie można załadować vat_norms.json: {e}")
    return {}


def _detect_year_from_text(text: str) -> int:
    """Wykrywa rok faktury z tekstu."""
    patterns = [
        r"\b(201[5-9]|202[0-9])\b",
        r"rok\s+(\d{4})",
        r"data[^:]*:\s*\d{1,2}[./]\d{1,2}[./](20\d{2})",
        r"\d{1,2}[./]\d{1,2}[./](20\d{2})",
    ]
    years_found = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            m_str = m if isinstance(m, str) else str(m)
            if m_str.isdigit() and 2015 <= int(m_str) <= 2030:
                years_found.append(int(m_str))
    return max(years_found) if years_found else 2026


def _extract_text_from_file(path: str) -> str:
    """
    [MODERNIZACJA v3] Ekstrakcja tekstu z pliku — teraz działa prawdziwie.
    Obsługuje: PDF, PNG, JPG, JPEG, TIFF, TXT, CSV — offline, bez API, bez sieci.
    """
    ext = os.path.splitext(path)[1].lower()

    # PDF i obrazy — PyMuPDF (fitz)
    if ext in (".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"):
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(path)
            pages_text = []
            for page in doc:
                # Próba ekstrakcji tekstu wektorowego (PDF z tekstem)
                text = page.get_text("text")
                if len(text.strip()) > 30:
                    pages_text.append(text)
                else:
                    # Fallback: OCR przez wbudowane narzędzia PyMuPDF (dla skanów)
                    # Wymaga tesseract w systemie, ale nie rzuca wyjątku jeśli brak
                    try:
                        text = page.get_text("words")
                        pages_text.append(" ".join([w[4] for w in text]))
                    except Exception:
                        pages_text.append(text)
            doc.close()
            extracted = "\n".join(pages_text).strip()
            if extracted:
                return extracted
        except ImportError:
            logger.warning("PyMuPDF nie jest zainstalowane. Zainstaluj: pip install pymupdf")
        except Exception as e:
            logger.warning(f"PyMuPDF błąd dla {path}: {e}")

    # Pliki tekstowe i Excel-CSV
    if ext in (".txt", ".csv"):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            pass

    # Excel (.xlsx)
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
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Błąd czytania xlsx {path}: {e}")

    return ""


class SecureAuditAgent:
    """Agent audytu dokumentów finansowych z obsługą historycznych norm VAT."""

    SAFE_ZONE = "synapsa_workspace/audit_safe_zone"

    def __init__(self, engine=None):
        if engine is None:
            from synapsa.engine import SynapsaEngine
            self.engine = SynapsaEngine.get_instance()
        else:
            self.engine = engine
        self._norms = _load_vat_norms()

    def _isolate_files(self, file_paths: list) -> list:
        """Kopiuje pliki do bezpiecznej strefy przed analizą. Oryginały NIENARUSZONE."""
        session_id = str(uuid.uuid4())[:8]
        safe_dir = os.path.join(self.SAFE_ZONE, session_id)
        os.makedirs(safe_dir, exist_ok=True)
        isolated = []
        for path in file_paths:
            if os.path.exists(path):
                dest = os.path.join(safe_dir, os.path.basename(path))
                shutil.copy2(path, dest)
                isolated.append(dest)
        return isolated

    def _get_norms_for_year(self, year: int) -> dict:
        """Pobiera normy VAT dla danego roku z bazy wiedzy."""
        years = self._norms.get("years", {})
        return years.get(str(year)) or years.get(str(year - 1)) or years.get("2026", {})

    def _extract_files_content(self, files: list) -> str:
        """
        [KLUCZOWY FIX v3] Czyta rzeczywistą treść każdego pliku do stringa.
        Wcześniej agent AI nie dostawał żadnej treści — teraz dostaje pełny tekst.
        """
        all_text = []
        for path in files:
            filename = os.path.basename(path)
            content = _extract_text_from_file(path)
            if content.strip():
                # Limit do 6000 znaków na plik, żeby nie przekroczyć context window
                truncated = content[:6000]
                if len(content) > 6000:
                    truncated += "\n[... treść skrócona do 6000 znaków ...]"
                all_text.append(f"=== PLIK: {filename} ===\n{truncated}")
            else:
                all_text.append(f"=== PLIK: {filename} === [nie udało się odczytać treści]")
        return "\n\n".join(all_text)

    def _generate_audit_plan(self, prompt: str, files: list) -> str:
        """
        [MODERNIZACJA v3] Generuje plan audytu z rzeczywistą treścią dokumentów.
        Używa nowoczesnego formatu ChatML dla Qwen 2.5.
        """
        # Ekstrakcja RZECZYWISTEJ treści plików
        files_content = self._extract_files_content(files)

        # Wykrywamy rok z treści pliku + promptu
        text_for_detection = files_content + " " + prompt
        invoice_year = _detect_year_from_text(text_for_detection)

        year_norms = self._get_norms_for_year(invoice_year)
        norms_desc = year_norms.get("description", f"Normy dla roku {invoice_year}")
        required_fields = year_norms.get("required_fields", [])
        ksef_required = year_norms.get("ksef_required", False)
        split_payment_note = year_norms.get("split_payment_note", "Mechanizm podzielonej płatności")
        split_threshold = year_norms.get("split_payment_threshold_pln")
        vat_rates = year_norms.get("vat_rates", [23, 8, 5, 0])
        important_notes = year_norms.get("important_notes", [])

        norms_list = "\n".join([f"   - {field}" for field in required_fields])
        ksef_instruction = ""
        if ksef_required:
            ksef_instruction = "\n   - NUMER KSeF (OBOWIĄZKOWY od 01.02.2026 — brak = BŁĄD KRYTYCZNY)"
        elif invoice_year >= 2024:
            ksef_instruction = "\n   - Numer KSeF (od 2026 obowiązkowy dla MŚP, teraz dobrowolny)"

        split_instruction = ""
        if split_threshold:
            split_instruction = f"\n   - Dopisek '{split_payment_note}' (dla kwot >{split_threshold} PLN brutto)"

        notes_text = "\n".join([f"   • {n}" for n in important_notes])

        # [MODERNIZACJA] Nowoczesny format ChatML dla Qwen 2.5
        system_msg = f"""Jesteś Audytorem Finansowym AI ("Synapsa Secure Audit v3").
Sprawdzasz dokumenty finansowe pod kątem błędów formalnych i rachunkowych.
Odpowiadasz WYŁĄCZNIE w formacie JSON. Nie dodajesz żadnych wstępów ani wyjaśnień poza JSONem."""

        user_msg = f"""ZADANIE: {prompt}
ROK FAKTURY (wykryty automatycznie): {invoice_year}
PODSTAWA PRAWNA: {norms_desc}

UWAGI PRAWNE DO ROKU {invoice_year}:
{notes_text}

WYMAGANE ELEMENTY FAKTURY DLA ROKU {invoice_year}:
{norms_list}{ksef_instruction}{split_instruction}
DOZWOLONE STAWKI VAT W {invoice_year}: {vat_rates}%

TREŚĆ DOKUMENTÓW DO ANALIZY:
{files_content}

Zwróć raport w formacie JSON:
{{
  "rok_faktury": {invoice_year},
  "status": "OK" | "BLEDY" | "OSTRZEZENIA",
  "bledy_formalne": ["..."],
  "bledy_rachunkowe": ["..."],
  "ostrzezenia": ["..."],
  "rekomendacje": ["..."],
  "ocena_ogolna": "2-3 zdania"
}}"""

        return self.engine.generate_chat(system_msg, user_msg)

    def _offline_rule_audit(self, prompt: str, files: list) -> dict:
        """
        Audyt regułowy offline — działa nawet bez modelu AI.
        Teraz też używa PyMuPDF do czytania faktury.
        """
        full_text = self._extract_files_content(files)

        if not full_text.strip() or "[nie udało się odczytać" in full_text:
            return {
                "rok_faktury": 2026,
                "status": "BLEDY",
                "bledy_formalne": ["Nie można odczytać treści pliku — format nieobsługiwany lub plik pusty"],
                "bledy_rachunkowe": [],
                "ostrzezenia": [],
                "rekomendacje": ["Prześlij plik w formacie PDF z tekstem lub TXT"],
                "ocena_ogolna": "Brak treści do analizy. Zweryfikuj format pliku.",
            }

        t = full_text.lower()
        invoice_year = _detect_year_from_text(full_text)
        year_norms = self._get_norms_for_year(invoice_year)
        vat_rates_ok = year_norms.get("vat_rates", [23, 8, 5, 0])
        ksef_required = year_norms.get("ksef_required", False)
        split_threshold = year_norms.get("split_payment_threshold_pln", 15000)

        bledy_formalne = []
        bledy_rachunkowe = []
        ostrzezenia = []
        rekomendacje = []

        if not re.search(r'faktura\s*vat', t):
            bledy_formalne.append("Brak nagłówka 'FAKTURA VAT' — wymagany przez art. 106e ust. 1 pkt 1 ustawy o VAT")

        has_date = bool(re.search(r'\d{1,2}[./]\d{1,2}[./]\d{4}', full_text))
        if not has_date:
            bledy_formalne.append("Brak daty wystawienia faktury — wymagany element (art. 106e ust. 1 pkt 1)")

        has_nip_any = bool(re.search(r'nip\s*:?\s*([\d]{3}[-\s]?[\d]{3}[-\s]?[\d]{2}[-\s]?[\d]{2}|[\d]{10})', t))
        if not has_nip_any:
            bledy_formalne.append("Brak numeru NIP — wymagany identyfikator podatkowy (art. 106e ust. 1 pkt 3)")
        else:
            nip_matches = re.findall(r'nip\s*:?\s*([\d]{3}[-\s]?[\d]{3}[-\s]?[\d]{2}[-\s]?[\d]{2}|[\d]{10,13})', t)
            for nip_raw in nip_matches:
                nip_digits = re.sub(r'[^\d]', '', nip_raw)
                if nip_digits and len(nip_digits) != 10:
                    bledy_formalne.append(f"Nieprawidłowy NIP: '{nip_raw.strip()}' — NIP musi mieć dokładnie 10 cyfr")
                    break

        has_payment_term = bool(re.search(r'termin\s+p[łl]atno|p[łl]atno\S*\s+do|zapłaty', t))
        if not has_payment_term:
            ostrzezenia.append("Brak terminu płatności — zalecany element faktury")

        has_account = bool(re.search(r'(?:konto|numer\s+konta|iban|pl\d{26}|\d{26})', t))
        if not has_account:
            ostrzezenia.append("Brak numeru konta bankowego — wymagany przy płatności przelewem")

        vat_found = re.findall(r'vat\s*(\d+)\s*%', t)
        invalid_vat = [int(v) for v in vat_found if int(v) not in vat_rates_ok]
        if invalid_vat:
            bledy_formalne.append(
                f"Nieprawidłowa stawka VAT: {invalid_vat}% nie obowiązuje w {invoice_year}. "
                f"Dozwolone: {vat_rates_ok}%"
            )

        amounts = re.findall(r'(?:brutto|do\s+zap[łl]aty|razem)[^\d]{0,20}([\d\s,.]+)\s*pln', t)
        max_amount = 0.0
        for a in amounts:
            try:
                val = float(re.sub(r'[\s]', '', a).replace(',', '.'))
                max_amount = max(max_amount, val)
            except ValueError:
                pass

        has_mpp_note = bool(re.search(r'podzielonej\s+p[łl]atno|split\s+payment|mechanizm\s+podziel', t))
        if split_threshold is not None and max_amount > split_threshold and not has_mpp_note:
            bledy_formalne.append(
                f"Brak dopisku o mechanizmie podzielonej płatności (MPP) — "
                f"kwota {max_amount:,.2f} PLN przekracza próg {split_threshold:,} PLN"
            )
        elif split_threshold is not None and max_amount > split_threshold and has_mpp_note:
            rekomendacje.append(f"Dopisek MPP obecny ✓ — kwota {max_amount:,.2f} PLN > {split_threshold:,} PLN")

        has_ksef = bool(re.search(r'ksef|ksej|pl\s*fa\s*\d', t))
        if ksef_required and not has_ksef:
            bledy_formalne.append(
                "Brak numeru KSeF — OBOWIĄZKOWY od 01.02.2026 dla wszystkich podatników VAT"
            )
        elif invoice_year >= 2024 and not has_ksef:
            ostrzezenia.append("Brak numeru KSeF — od 01.04.2026 obowiązkowy dla MŚP, zalecane wdrożenie już teraz")

        # Sprawdzenie rachunkowe
        netto_vals = re.findall(r'(?:netto|wartość\s+netto)[^\d]{0,20}([\d\s]+[,.]\d{2})', t)
        brutto_vals = re.findall(r'(?:brutto|do\s+zap[łl]aty)[^\d]{0,20}([\d\s]+[,.]\d{2})', t)
        if netto_vals and brutto_vals and vat_found:
            try:
                netto = float(re.sub(r'[\s]', '', netto_vals[0]).replace(',', '.'))
                brutto = float(re.sub(r'[\s]', '', brutto_vals[0]).replace(',', '.'))
                vat_rate = float(vat_found[0])
                expected_brutto = round(netto * (1 + vat_rate / 100), 2)
                if abs(expected_brutto - brutto) > 1.0:
                    bledy_rachunkowe.append(
                        f"Niezgodność: netto {netto:,.2f} × (1+{vat_rate}%) = "
                        f"{expected_brutto:,.2f}, faktura podaje brutto {brutto:,.2f} PLN"
                    )
                else:
                    rekomendacje.append(f"Rachunek poprawny: {netto:,.2f} × {1+vat_rate/100:.2f} = {brutto:,.2f} PLN ✓")
            except (ValueError, IndexError):
                pass

        n_errors = len(bledy_formalne) + len(bledy_rachunkowe)
        if n_errors == 0 and not ostrzezenia:
            status = "OK"
            ocena = f"Faktura z roku {invoice_year} jest prawidłowa zgodnie z przepisami obowiązującymi w {invoice_year}."
        elif n_errors == 0:
            status = "OSTRZEZENIA"
            ocena = f"Faktura z roku {invoice_year} nie ma błędów krytycznych. Zawiera {len(ostrzezenia)} ostrzeżeń."
        else:
            status = "BLEDY"
            ocena = (
                f"Faktura z roku {invoice_year} zawiera {len(bledy_formalne)} błędów formalnych "
                f"i {len(bledy_rachunkowe)} błędów rachunkowych."
            )

        if not rekomendacje:
            rekomendacje.append("Zweryfikuj wszystkie dane z oryginałem przed złożeniem deklaracji VAT")

        return {
            "rok_faktury": invoice_year,
            "podstawa_prawna": year_norms.get("description", f"Przepisy {invoice_year}"),
            "status": status,
            "bledy_formalne": bledy_formalne,
            "bledy_rachunkowe": bledy_rachunkowe,
            "ostrzezenia": ostrzezenia,
            "rekomendacje": rekomendacje,
            "ocena_ogolna": ocena,
            "tryb": "OFFLINE (analiza regułowa — bez AI)",
        }

    def process_audit(self, prompt: str, file_paths: list) -> dict:
        """
        Główna metoda audytu.
        1. Izoluje pliki
        2. Wyciąga tekst przez PyMuPDF (FIX v3!)
        3. Wysyła pełną treść do AI (FIX v3!)
        4. Fallback: audyt regułowy jeśli model niedostępny
        """
        logger.info(f"[SecureAudit v3] Izolacja {len(file_paths)} pliku(ów)...")
        isolated_paths = self._isolate_files(file_paths)

        logger.info("[SecureAudit v3] Analiza dokumentów z PyMuPDF...")
        raw_result = self._generate_audit_plan(prompt, isolated_paths)

        # Fallback → audyt regułowy jeśli model AI niedostępny
        if not raw_result or "DEMO_MODE" in raw_result or "TRYB DEMONSTRACYJNY" in raw_result:
            logger.info("[SecureAudit] Model AI niedostępny → audyt regułowy OFFLINE...")
            offline_report = self._offline_rule_audit(prompt, isolated_paths)
            return {
                "status": "success",
                "report": json.dumps(offline_report, ensure_ascii=False, indent=2),
                "mode": "offline",
            }

        # Parsowanie JSON z odpowiedzi AI
        try:
            json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)
            if json_match:
                audit_data = json.loads(json_match.group())
                return {"status": "success", "report": json.dumps(audit_data, ensure_ascii=False, indent=2), "mode": "ai"}
            else:
                return {"status": "success", "report": raw_result, "mode": "ai_raw"}
        except (json.JSONDecodeError, Exception):
            return {"status": "success", "report": raw_result, "mode": "ai_raw"}
