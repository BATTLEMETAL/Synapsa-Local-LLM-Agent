"""
Synapsa — SecureAuditAgent (Rewrote from scratch)
Oparty na:
- Audytor.py (pętla poprawek, ekstrakacja kodu, generowanie analizy)
- Obserwator.py (wzorzec loading modelu)
- vat_norms.json (historyczne normy VAT 2018-2026)
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
    """
    Wykrywa rok faktury z tekstu.
    Wzorzec z office_agent.py (poprzednia wersja) + rozszerzony regex.
    """
    patterns = [
        r"\b(201[5-9]|202[0-9])\b",  # Szerokie dopasowanie
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

    return max(years_found) if years_found else 2026  # Domyślnie bieżący rok


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
        """
        Kopiuje pliki do bezpiecznej strefy przed analizą.
        Oryginały pozostają NIENARUSZONE. (Wzorzec z poprzedniej implementacji)
        """
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
        year_data = years.get(str(year)) or years.get(str(year - 1)) or years.get("2026", {})
        return year_data

    def _generate_audit_plan(self, prompt: str, files: list) -> str:
        """
        Generuje plan audytu z uwzględnieniem historycznych norm.
        Wykrywa rok faktury i stosuje odpowiednie przepisy.
        """
        # Wykrywamy rok z promptu
        text_for_detection = prompt + " ".join(os.path.basename(f) for f in files)
        invoice_year = _detect_year_from_text(text_for_detection)

        # Pobieramy normy dla tego roku
        year_norms = self._get_norms_for_year(invoice_year)
        norms_desc = year_norms.get("description", f"Normy dla roku {invoice_year}")
        required_fields = year_norms.get("required_fields", [])
        ksef_required = year_norms.get("ksef_required", False)
        split_payment_note = year_norms.get("split_payment_note", "Mechanizm podzielonej płatności")
        split_threshold = year_norms.get("split_payment_threshold_pln")
        vat_rates = year_norms.get("vat_rates", [23, 8, 5, 0])

        # Budujemy listę norm
        norms_list = "\n".join([f"   - [ ] {field}" for field in required_fields])

        ksef_instruction = ""
        if ksef_required:
            ksef_instruction = "\n   - [ ] NUMER KSeF (OBOWIĄZKOWY od 2026 — brak = BŁĄD KRYTYCZNY)"
        elif invoice_year >= 2024:
            ksef_instruction = "\n   - [ ] Numer KSeF (zalecany, obowiązkowy dla dużych firm)"

        split_instruction = ""
        if split_threshold:
            split_instruction = f"\n   - [ ] Dopisek '{split_payment_note}' (dla kwot >{split_threshold} PLN)"

        system_prompt = f"""Jesteś Audytorem Finansowym AI ("Synapsa Secure Audit v2").
Analizujesz dokumenty pod kątem błędów i niespójności.

ZADANIE: {prompt}
PLIKI DO ANALIZY: {', '.join([os.path.basename(f) for f in files])}
ROK FAKTURY (wykryty): {invoice_year}
PODSTAWA PRAWNA: {norms_desc}

ZASADY BEZWZGLĘDNE:
1. NIE modyfikuj oryginałów. Pracujesz NA KOPII.
2. Sprawdź faktury NA PODSTAWIE PRZEPISÓW Z ROKU {invoice_year} (NIE bieżących).
3. Nie zgłaszaj błędu braku KSeF dla faktur sprzed 2026 jeśli nie było obowiązku.
4. Stawki VAT dozwolone w {invoice_year}: {vat_rates}%

LISTA KONTROLNA (obowiązkowe elementy faktury dla roku {invoice_year}):
{norms_list}{ksef_instruction}{split_payment_note and split_instruction}

FORMAT RAPORTU (JSON):
{{
  "rok_faktury": {invoice_year},
  "status": "OK" | "BLEDY" | "OSTRZEZENIA",
  "bledy_formalne": ["Lista błędów — brakujące obowiązkowe pola"],
  "bledy_rachunkowe": ["Lista błędów rachunkowych"],
  "ostrzezenia": ["Lista ostrzeżeń (niekrytyczne)"],
  "rekomendacje": ["Lista zaleceń do poprawy"],
  "ocena_ogolna": "Opis w 2-3 zdaniach"
}}
"""
        return self.engine.generate(system_prompt, max_tokens=2000)

    def _offline_rule_audit(self, prompt: str, files: list) -> dict:
        """
        Audyt regułowy bez AI — czyta treść pliku i sprawdza zgodność z przepisami.
        Uruchamiany gdy model AI jest niedostępny (TRYB OFFLINE).
        Zwraca strukturę identyczną z formatem AI.
        """
        full_text = ""
        for path in files:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    full_text += f.read() + "\n"
            except Exception:
                pass

        if not full_text.strip():
            return {
                "rok_faktury": 2026,
                "status": "BLEDY",
                "bledy_formalne": ["Nie można odczytać treści pliku — format nieobsługiwany lub plik pusty"],
                "bledy_rachunkowe": [],
                "ostrzezenia": [],
                "rekomendacje": ["Prześlij plik w formacie TXT lub PDF z tekstem"],
                "ocena_ogolna": "Brak treści do analizy. Zweryfikuj format pliku.",
            }

        t = full_text.lower()

        # Wykryj rok faktury z treści pliku (nie tylko nazwy)
        invoice_year = _detect_year_from_text(full_text)
        year_norms = self._get_norms_for_year(invoice_year)
        vat_rates_ok = year_norms.get("vat_rates", [23, 8, 5, 0])
        ksef_required = year_norms.get("ksef_required", False)
        split_threshold = year_norms.get("split_payment_threshold_pln", 15000)

        bledy_formalne = []
        bledy_rachunkowe = []
        ostrzezenia = []
        rekomendacje = []

        # ── 1. WYMAGANE POLA FORMY ─────────────────────────────────
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
                    bledy_formalne.append(
                        f"Nieprawidłowy NIP: '{nip_raw.strip()}' — NIP musi mieć dokładnie 10 cyfr"
                    )
                    break

        has_payment_term = bool(re.search(r'termin\s+p[łl]atno|p[łl]atno\S*\s+do|zapłaty', t))
        if not has_payment_term:
            ostrzezenia.append("Brak terminu płatności — zalecany element faktury")

        has_account = bool(re.search(r'(?:konto|numer\s+konta|iban|pl\d{26}|\d{26})', t))
        if not has_account:
            ostrzezenia.append("Brak numeru konta bankowego — wymagany przy płatności przelewem")

        # ── 2. STAWKI VAT ──────────────────────────────────────────
        vat_found = re.findall(r'vat\s*(\d+)\s*%', t)
        invalid_vat = [int(v) for v in vat_found if int(v) not in vat_rates_ok]
        if invalid_vat:
            bledy_formalne.append(
                f"Nieprawidłowa stawka VAT: {invalid_vat}% nie obowiązuje w {invoice_year}. "
                f"Dozwolone: {vat_rates_ok}%"
            )

        # ── 3. MECHANIZM PODZIELONEJ PŁATNOŚCI (MPP) ─────────────
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
                f"kwota {max_amount:,.2f} PLN przekracza próg {split_threshold:,} PLN (art. 108a ustawy o VAT)"
            )
        elif split_threshold is not None and max_amount > split_threshold and has_mpp_note:
            rekomendacje.append(f"Dopisek MPP obecny ✓ — kwota {max_amount:,.2f} PLN > {split_threshold:,} PLN")

        # ── 4. KSeF ────────────────────────────────────────────────
        has_ksef = bool(re.search(r'ksef|ksej|pl\s*fa\s*\d', t))
        if ksef_required and not has_ksef:
            bledy_formalne.append(
                "Brak numeru KSeF — OBOWIĄZKOWY od 2026 roku dla wszystkich faktur VAT "
                "(ustawa z dnia 16.06.2023 o zmianie ustawy o VAT)"
            )
        elif invoice_year >= 2024 and not has_ksef:
            ostrzezenia.append("Brak numeru KSeF — od 2024 roku zalecany dla aktywnych podatników VAT")

        # ── 5. SPRAWDZENIE RACHUNKOWE ──────────────────────────────
        netto_vals = re.findall(r'(?:netto|wartość\s+netto)[^\d]{0,20}([\d\s]+[,.][\d]{2})', t)
        brutto_vals = re.findall(r'(?:brutto|do\s+zap[łl]aty)[^\d]{0,20}([\d\s]+[,.][\d]{2})', t)

        if netto_vals and brutto_vals and vat_found:
            try:
                netto = float(re.sub(r'[\s]', '', netto_vals[0]).replace(',', '.'))
                brutto = float(re.sub(r'[\s]', '', brutto_vals[0]).replace(',', '.'))
                vat_rate = float(vat_found[0])
                expected_brutto = round(netto * (1 + vat_rate / 100), 2)
                if abs(expected_brutto - brutto) > 1.0:
                    bledy_rachunkowe.append(
                        f"Niezgodność rachunkowa: netto {netto:,.2f} × (1+{vat_rate}%) = "
                        f"{expected_brutto:,.2f} PLN, lecz faktura podaje brutto {brutto:,.2f} PLN"
                    )
                else:
                    rekomendacje.append(f"Rachunek poprawny: {netto:,.2f} × {1+vat_rate/100:.2f} = {brutto:,.2f} PLN ✓")
            except (ValueError, IndexError):
                pass

        # ── 6. OCENA OGÓLNA ────────────────────────────────────────
        n_errors = len(bledy_formalne) + len(bledy_rachunkowe)
        if n_errors == 0 and not ostrzezenia:
            status = "OK"
            ocena = (
                f"Faktura z roku {invoice_year} nie zawiera wykrytych błędów. "
                f"Spełnia wymogi przepisów obowiązujących w roku {invoice_year}."
            )
        elif n_errors == 0:
            status = "OSTRZEZENIA"
            ocena = (
                f"Faktura z roku {invoice_year} nie ma błędów krytycznych, "
                f"ale zawiera {len(ostrzezenia)} ostrzeżeń do weryfikacji."
            )
        else:
            status = "BLEDY"
            ocena = (
                f"Faktura z roku {invoice_year} zawiera {len(bledy_formalne)} błędów formalnych "
                f"i {len(bledy_rachunkowe)} błędów rachunkowych wymagających korekty."
            )

        if not rekomendacje:
            rekomendacje.append("Zweryfikuj wszystkie dane z oryginałem dokumentu przed złożeniem deklaracji VAT")

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
        1. Izoluje pliki (kopia do safe_zone)
        2. Próbuje AI → jeśli DEMO_MODE → przełącza na audyt regułowy
        3. Generuje raport
        """
        print(f"🔒 [SecureAudit] Izolacja {len(file_paths)} pliku(ów)...", flush=True)
        isolated_paths = self._isolate_files(file_paths)

        print(f"🕵️  [SecureAudit] Analiza dokumentów...", flush=True)
        raw_result = self._generate_audit_plan(prompt, isolated_paths)

        # Jeśli model AI zwrócił DEMO_MODE → użyj audytu regułowego
        if "DEMO_MODE" in raw_result or "TRYB DEMONSTRACYJNY" in raw_result:
            print("📋 [SecureAudit] Model AI niedostępny — uruchamiam audyt regułowy OFFLINE...", flush=True)
            offline_report = self._offline_rule_audit(prompt, isolated_paths)
            return {
                "status": "success",
                "report": json.dumps(offline_report, ensure_ascii=False, indent=2),
            }

        # Próba parsowania JSON z odpowiedzi AI
        try:
            json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)
            if json_match:
                audit_data = json.loads(json_match.group())
                return {"status": "success", "report": json.dumps(audit_data, ensure_ascii=False, indent=2)}
            else:
                return {"status": "success", "report": raw_result}
        except (json.JSONDecodeError, Exception):
            return {"status": "success", "report": raw_result}
