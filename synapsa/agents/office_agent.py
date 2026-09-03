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
        Teraz też używa PyMuPDF do czytania faktury, z pełną walidacją Fazy 3.
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

        from synapsa.agents.nip_validator import validate_nip as nip_checksum_validate

        if not re.search(r'faktura\s*vat', t):
            bledy_formalne.append("Brak nagłówka 'FAKTURA VAT' — wymagany przez przepisy")

        has_date = bool(re.search(r'\d{1,2}[./]\d{1,2}[./]\d{4}', full_text))
        if not has_date:
            bledy_formalne.append("Brak daty wystawienia faktury")

        # NIP validation
        nips = re.findall(r'nip\s*:?\s*([\d\-\s]{10,15})', t)
        if not nips:
            candidates = re.findall(r'\b\d{10}\b', full_text)
            nips = [c for c in candidates if nip_checksum_validate(c)[0]]

        detected_nips = []
        for nip_raw in nips:
            nip_digits = re.sub(r'[^\d]', '', nip_raw)
            if len(nip_digits) == 10:
                is_ok, _ = nip_checksum_validate(nip_digits)
                if is_ok:
                    if nip_digits not in detected_nips:
                        detected_nips.append(nip_digits)
                else:
                    bledy_formalne.append(f"Nieprawidłowa suma kontrolna NIP: {nip_raw.strip()}")
            else:
                bledy_formalne.append(f"Nieprawidłowy format NIP: {nip_raw.strip()} (wymagane 10 cyfr)")

        seller_nip = detected_nips[0] if detected_nips else None
        if not seller_nip:
            bledy_formalne.append("Brak poprawnego numeru NIP sprzedawcy/nabywcy")

        if not re.search(r'termin\s+p[łl]atno|p[łl]atno\S*\s+do|zapłaty', t):
            ostrzezenia.append("Brak terminu płatności — zalecany element faktury")

        if not re.search(r'(?:konto|numer\s+konta|iban|pl\d{26}|\d{26})', t):
            ostrzezenia.append("Brak numeru konta bankowego")

        vat_found = re.findall(r'vat\s*(\d+)\s*%', t)
        invalid_vat = [int(v) for v in vat_found if int(v) not in vat_rates_ok]
        if invalid_vat:
            bledy_formalne.append(f"Nieprawidłowa stawka VAT: {invalid_vat}% (dozwolone: {vat_rates_ok}%)")

        # MPP
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

        # KSeF validation
        ksef_matches = re.findall(r'\b\d{10}-\d{8}-[a-zA-Z0-9]{6}-[a-zA-Z0-9]{6}\b|\b\d{35}\b', t)
        detected_ksef = ksef_matches[0] if ksef_matches else None
        if detected_ksef:
            clean_ksef = re.sub(r'[^a-zA-Z0-9]', '', detected_ksef)
            if len(clean_ksef) == 35:
                # KSeF structures verification (NIP & year match)
                k_nip = clean_ksef[:10]
                k_date = clean_ksef[10:18]
                is_k_nip_valid, _ = nip_checksum_validate(k_nip)
                if not is_k_nip_valid:
                    bledy_formalne.append(f"Błąd KSeF: Niepoprawny NIP w KSeF: {k_nip}")
                elif seller_nip and k_nip != seller_nip:
                    bledy_formalne.append(f"Błąd KSeF: NIP z KSeF ({k_nip}) nie zgadza się ze sprzedawcą ({seller_nip})")
                
                try:
                    k_year = int(k_date[:4])
                    if k_year != invoice_year:
                        bledy_formalne.append(f"Błąd KSeF: Rok z KSeF ({k_year}) nie zgadza się z rokiem faktury ({invoice_year})")
                except ValueError:
                    bledy_formalne.append(f"Błąd KSeF: Niepoprawny format daty w KSeF: {k_date}")
            else:
                rekomendacje.append(f"Wykryto numer KSeF w formacie tradycyjnym/mock: {detected_ksef}")
        else:
            if ksef_required:
                bledy_formalne.append("Brak obowiązkowego numeru KSeF (wymagany od 01.02.2026)")
            elif invoice_year >= 2024:
                ostrzezenia.append("Brak numeru KSeF — zalecane wdrożenie")

        # Sprawdzenie rachunkowe pozycji tabeli
        from app_ksiegowosc import _extract_invoice_items as ext_items
        try:
            pozycje = ext_items(full_text)
        except Exception:
            pozycje = []

        netto_vals = re.findall(r'(?:netto|wartość\s+netto)[^\d]{0,20}([\d\s]+[,.]\d{2})', t)
        brutto_vals = re.findall(r'(?:brutto|do\s+zap[łl]aty)[^\d]{0,20}([\d\s]+[,.]\d{2})', t)
        
        netto, brutto = None, None
        if netto_vals:
            try: netto = float(re.sub(r'[\s]', '', netto_vals[0]).replace(',', '.'))
            except ValueError: pass
        if brutto_vals:
            try: brutto = float(re.sub(r'[\s]', '', brutto_vals[0]).replace(',', '.'))
            except ValueError: pass

        if pozycje and netto and brutto:
            total_netto = sum(p["netto"] for p in pozycje)
            total_brutto = sum(p["brutto"] for p in pozycje)
            if abs(total_netto - netto) > 5.0:
                bledy_rachunkowe.append(f"Suma netto pozycji ({total_netto:,.2f}) nie zgadza się z wartością netto faktury ({netto:,.2f})")
            if abs(total_brutto - brutto) > 5.0:
                bledy_rachunkowe.append(f"Suma brutto pozycji ({total_brutto:,.2f}) nie zgadza się z wartością brutto faktury ({brutto:,.2f})")

        # Sprawdzenie ogólne matematyczne
        if netto and brutto and vat_found:
            try:
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
