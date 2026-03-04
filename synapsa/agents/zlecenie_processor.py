"""
Synapsa — ZlecenieProcessor
Przetwarza zlecenie w języku naturalnym → kosztorys → faktura.

Wzorzec: Użytkownik pisze: "mam nowe zlecenie budowanie kostki brukowej,
cena 150 za metr kwadratowy" — system oblicza wszystko i wystawia fakturę
w stylu poprzednich faktur klienta (lub domyślnym jeśli brak).
"""
import re
import json
import os
import logging
from datetime import date

logger = logging.getLogger(__name__)

# Słownik typów prac budowlanych → stawka VAT
PRACA_VAT_MAP = {
    # 8% VAT — budownictwo mieszkaniowe (art. 41 ust. 12 ustawy o VAT)
    "ocieplenie": 8,
    "izolacja": 8,
    "tynk": 8,
    "tynkowanie": 8,
    "malowanie": 8,
    "remont": 8,
    "modernizacja": 8,
    "przebudowa": 8,
    "adaptacja": 8,
    "docieplenie": 8,
    "elewacja": 8,
    # 23% VAT — nowe budownictwo, usługi niemieszkaniowe
    "kostka": 23,
    "kostka brukowa": 23,
    "bruk": 23,
    "parking": 23,
    "droga": 23,
    "chodnik": 23,
    "ogrodzenie": 23,
    "projekt": 23,
    "instalacja elektryczna": 23,
    "instalacja": 23,
    "fotowoltaika": 23,
    "pompa ciepła": 23,
    "dach": 23,
    "pokrycie dachu": 23,
    "fundamenty": 23,
    "wylewka": 23,
    "budowa": 23,
    "konstrukcja": 23,
    "nowa": 23,
    "nowe": 23,
}

# Słownik materiałów → koszt materiałów jako % ceny końcowej
MATERIAL_RATIO = {
    "kostka brukowa": 0.55,  # materiały: ~55% ceny, robocizna: ~45%
    "kostka": 0.55,
    "bruk": 0.55,
    "styropian": 0.50,
    "ocieplenie": 0.50,
    "dachówka": 0.60,
    "dach": 0.60,
    "tynk": 0.35,
    "tynkowanie": 0.35,
    "wylewka": 0.45,
    "instalacja": 0.40,
    "default": 0.50,
}

COUNTER_ID_FILE = "synapsa_workspace/invoice_counter.json"


def _next_invoice_number() -> str:
    """Generuje kolejny numer faktury FV/RRRR/NNN."""
    os.makedirs("synapsa_workspace", exist_ok=True)
    counter = {"year": date.today().year, "n": 0}
    if os.path.exists(COUNTER_ID_FILE):
        try:
            with open(COUNTER_ID_FILE) as f:
                counter = json.load(f)
        except Exception:
            pass
    if counter.get("year") != date.today().year:
        counter = {"year": date.today().year, "n": 0}
    counter["n"] += 1
    with open(COUNTER_ID_FILE, "w") as f:
        json.dump(counter, f)
    return f"FV/{counter['year']}/{counter['n']:03d}"


class ZlecenieParser:
    """
    Parsuje opis zlecenia w języku naturalnym i wyodrębnia kluczowe dane.
    Działa w pełni offline — bez AI.
    """

    def parse(self, text: str) -> dict:
        """
        Zwraca słownik z:
          - typ_pracy: str
          - metraz: float (m² lub mb)
          - cena_za_m2: float (PLN)
          - jednostka: str ('m²', 'mb', 'szt', 'komplet')
          - vat_rate: int (8 lub 23)
          - material_ratio: float
          - raw: str (oryginalny tekst)
        """
        text_lower = text.lower()

        typ_pracy = self._detect_work_type(text_lower)
        metraz = self._extract_area(text_lower)
        cena = self._extract_price(text_lower)
        jednostka = self._detect_unit(text_lower)
        vat = self._detect_vat(typ_pracy, text_lower)
        mat_ratio = self._detect_material_ratio(typ_pracy)

        return {
            "typ_pracy": typ_pracy,
            "metraz": metraz,
            "cena_za_m2": cena,
            "jednostka": jednostka,
            "vat_rate": vat,
            "material_ratio": mat_ratio,
            "raw": text,
        }

    def _detect_work_type(self, t: str) -> str:
        priority = [
            "kostka brukowa", "pompa ciepła", "instalacja elektryczna", "pokrycie dachu",
            "kostka", "ocieplenie", "tynkowanie", "malowanie", "wylewka", "izolacja",
            "elewacja", "dach", "remont", "budowa", "instalacja", "fundamenty",
            "parking", "droga", "chodnik", "ogrodzenie", "projekt",
        ]
        for p in priority:
            if p in t:
                return p
        # Fallback: weź pierwsze niezwykłe słowo rzeczownikowe
        words = re.findall(r'\b[a-ząćęłńóśźż]{4,}\b', t)
        skip = {"nowe", "nowa", "mamy", "mam", "jest", "zlecenie", "koszt", "cena",
                 "prace", "pracy", "metr", "kwadratowy", "budowanie", "proszę"}
        for w in words:
            if w not in skip:
                return w
        return "prace budowlane"

    def _extract_area(self, t: str) -> float:
        patterns = [
            r'(\d+(?:[,.]\d+)?)\s*m(?:etr(?:ów|ach|ów)?)?\s*kwadratowyc?h?',
            r'(\d+(?:[,.]\d+)?)\s*m[²2]',
            r'(\d+(?:[,.]\d+)?)\s*mb',
            r'(\d+(?:[,.]\d+)?)\s*metr',
            r'na\s+(\d+(?:[,.]\d+)?)',
            r'(\d+(?:[,.]\d+)?)\s*m\b',
        ]
        for p in patterns:
            m = re.search(p, t)
            if m:
                return float(m.group(1).replace(',', '.'))
        return 0.0

    def _extract_price(self, t: str) -> float:
        """
        Wyodrębnia cenę za m² lub cenę całkowitą.
        UWAGA: Musi ignorować wymiary grubości (np. '15cm' jest grubością, nie ceną)
        """
        # KROK 1: Usuń grubości (np. '15cm', '10cm', '200mm') aby nie mylić z cenami
        t_clean = re.sub(r'\d+\s*(?:cm|mm|cal)\b', 'GRUB', t)

        # KROK 2: Wzorce od najbardziej precyzyjnych do ogólnych
        patterns = [
            # 'cena 150 PLN za m', 'stawka 85 zl za m', 'za 120 PLN/m2'
            r'(?:cena|koszt|stawka|za)\s+(\d+(?:[,.]\d+)?)\s*(?:pln|zł|zl|złoty|złotych)?\s*(?:/|za)?\s*m',
            # '150 PLN za m', '85 zł/m2'
            r'(\d+(?:[,.]\d+)?)\s*(?:pln|zł|zl)\s+za\s*m',
            r'(\d+(?:[,.]\d+)?)\s*(?:pln|zł|zl)/m',
            # 'za metr 150', 'za m2 85'
            r'za\s+(?:metr|m[²2]?)\s+(\d+(?:[,.]\d+)?)',
            # Ogólnie: liczba z PLN/zł (minimum 10 PLN)
            r'(\d{2,}(?:[,.]\d+)?)\s*(?:pln|zł|zl)\b',
            # Komplet — cała kwota bez jednostki
            r'(\d{3,}(?:[,.]\d+)?)\s*(?:pln|zł|zl)?\s*(?:komplet|całość|ryczałt)',
        ]
        for p in patterns:
            m = re.search(p, t_clean)
            if m:
                v = float(m.group(1).replace(',', '.'))
                if v >= 10:  # realna cena musi być >= 10 PLN
                    return v

        # KROK 3: Ostatnia szansa — wszystkie liczby > 10 (z wyjątkiem typowych grubości)
        # Usuń grubości jak 15cm, 10cm, ale też wielokrotności metrów jak 80m2, 200m2
        t_nogrub = re.sub(r'\d+\s*(?:cm|mm|m[²2]|m2|mb|metr\w*)\b', 'WYM', t_clean)
        nums = [float(n.replace(',', '.')) for n in re.findall(r'\d+(?:[,.]\d+)?', t_nogrub)]
        for n in sorted(set(nums), reverse=True):  # od największej — bardziej prawdopodobne ceny
            if n >= 10:
                return n
        return 0.0

    def _detect_unit(self, t: str) -> str:
        if 'mb' in t or 'metr bieżący' in t:
            return 'mb'
        if 'szt' in t or 'sztuk' in t:
            return 'szt'
        if 'komplet' in t:
            return 'komplet'
        return 'm²'

    def _detect_vat(self, typ_pracy: str, text: str) -> int:
        # Explicite w tekście
        if '23%' in text or 'vat 23' in text:
            return 23
        if '8%' in text or 'vat 8' in text:
            return 8
        # Na podstawie typu pracy
        for kw, vat in PRACA_VAT_MAP.items():
            if kw in typ_pracy.lower() or kw in text:
                return vat
        return 23  # Default: 23%

    def _detect_material_ratio(self, typ_pracy: str) -> float:
        for kw, ratio in MATERIAL_RATIO.items():
            if kw in typ_pracy.lower():
                return ratio
        return MATERIAL_RATIO["default"]


class ZlecenieCalculator:
    """
    Oblicza pełny kosztorys na podstawie sparsowanego zlecenia.
    """

    def calculate(self, parsed: dict) -> dict:
        """
        Zwraca kosztorys:
          - netto: float
          - vat_kwota: float
          - brutto: float
          - materialy_netto: float
          - robocizna_netto: float
          - vat_rate: int
          - mpp_required: bool (>15000 PLN brutto)
          - pozycje: list[dict]
        """
        metraz = parsed["metraz"]
        cena_m2 = parsed["cena_za_m2"]
        vat_rate = parsed["vat_rate"]
        mat_ratio = parsed["material_ratio"]
        typ = parsed["typ_pracy"]
        jednostka = parsed["jednostka"]

        # Obliczenia
        is_komplet = jednostka == 'komplet'
        if is_komplet and cena_m2 > 0:
            # Cena 'komplet' = całkowita wartość netto (nie mnożymy przez metraż)
            netto = round(cena_m2, 2)
        elif metraz > 0 and cena_m2 > 0:
            netto = round(metraz * cena_m2, 2)
        elif cena_m2 > 0:
            netto = cena_m2
        else:
            netto = 0.0

        mat_netto = round(netto * mat_ratio, 2)
        rob_netto = round(netto - mat_netto, 2)
        vat_kwota = round(netto * vat_rate / 100, 2)
        brutto = round(netto + vat_kwota, 2)
        mpp = brutto >= 15000

        pozycje = []
        if metraz > 0:
            pozycje.append({
                "opis": f"{typ.title()} — {metraz} {jednostka}",
                "ilosc": metraz,
                "jednostka": jednostka,
                "cena_j": cena_m2,
                "netto": netto,
            })
        else:
            pozycje.append({
                "opis": f"{typ.title()} — usługa kompletna",
                "ilosc": 1,
                "jednostka": "komplet",
                "cena_j": cena_m2,
                "netto": netto,
            })

        return {
            "netto": netto,
            "vat_rate": vat_rate,
            "vat_kwota": vat_kwota,
            "brutto": brutto,
            "materialy_netto": mat_netto,
            "robocizna_netto": rob_netto,
            "mpp_required": mpp,
            "pozycje": pozycje,
            "typ_pracy": typ,
            "metraz": metraz,
            "jednostka": jednostka,
            "cena_m2": cena_m2,
        }

    def format_kosztorys(self, calc: dict) -> str:
        """Formatuje kosztorys w czytelny tekst."""
        lines = [
            f"📋 **KOSZTORYS — {calc['typ_pracy'].upper()}**",
            f"",
            f"| Pozycja | Wartość |",
            f"|---|---|",
        ]
        if calc["metraz"] > 0:
            lines.append(f"| Powierzchnia | {calc['metraz']:,.0f} {calc['jednostka']} |")
            lines.append(f"| Cena jednostkowa | {calc['cena_m2']:,.2f} PLN/{calc['jednostka']} |")

        lines += [
            f"| **Materiały netto** | {calc['materialy_netto']:,.2f} PLN |",
            f"| **Robocizna netto** | {calc['robocizna_netto']:,.2f} PLN |",
            f"| **Razem netto** | {calc['netto']:,.2f} PLN |",
            f"| VAT {calc['vat_rate']}% | {calc['vat_kwota']:,.2f} PLN |",
            f"| **BRUTTO** | **{calc['brutto']:,.2f} PLN** |",
        ]
        if calc["mpp_required"]:
            lines.append(f"| ⚠️ **MPP** | Mechanizm podzielonej płatności OBOWIĄZKOWY |")

        return "\n".join(lines)


class ZlecenieProcessor:
    """
    Główny procesor zleceń — łączy parser, kalkulator i agenta księgowego.

    Użycie:
        processor = ZlecenieProcessor()
        result = processor.process("mam nowe zlecenie budowanie kostki brukowej, cena 150 za m2")
        # result["kosztorys"] — tekst
        # result["faktura"] — tekst
        # result["parse"] — dict z danymi
        # result["calc"] — dict z obliczeniami
    """

    def __init__(self, engine=None, accountant_agent=None, lazy=True):
        self.parser = ZlecenieParser()
        self.calculator = ZlecenieCalculator()
        self.engine = engine
        self._accountant = accountant_agent  # None = lazy load on first use
        self._lazy = lazy

        if not lazy and accountant_agent is None:
            # Eager loading — załaduj teraz (np. dla testów)
            self._ensure_accountant()

    def _ensure_accountant(self):
        """Ładuje AccountantAgent dopiero gdy potrzebny (lazy)."""
        if self._accountant is None:
            try:
                from synapsa.agents.accountant_agent import AccountantAgent
                self._accountant = AccountantAgent(engine=self.engine)
            except Exception as e:
                logger.warning(f"Brak agenta księgowego: {e}")
                self._accountant = None

    @property
    def accountant(self):
        self._ensure_accountant()
        return self._accountant

    def process(self, zlecenie_text: str, nabywca: str = "", sprzedawca: str = "") -> dict:
        """
        Przetwarza zlecenie w języku naturalnym.
        Zwraca: {status, parse, calc, kosztorys_text, faktura_text, invoice_nr, error}
        """
        try:
            # KROK 1: Parsowanie
            parsed = self.parser.parse(zlecenie_text)
            logger.info(f"Parsed: {parsed}")

            # Walidacja
            if parsed["cena_za_m2"] <= 0:
                return {
                    "status": "error",
                    "error": "Nie udało się wykryć ceny. Podaj np. 'cena 150 PLN za m²' lub '150 zł/m²'.",
                    "parse": parsed,
                }

            # KROK 2: Obliczenia
            calc = self.calculator.calculate(parsed)
            kosztorys_text = self.calculator.format_kosztorys(calc)

            # KROK 3: Dane do faktury
            invoice_nr = _next_invoice_number()
            today = date.today().strftime("%d.%m.%Y")

            # Komentarz o stylu (z nauczonych faktur lub domyślny)
            style_info = ""
            if self.accountant and self.accountant.style.get("rules"):
                style_info = f"\nSTYL (z poprzednich faktur klienta):\n{self.accountant.style['rules']}"
            else:
                style_info = "\nSTYL: Standardowa polska faktura VAT — dane sprzedawcy u góry, tabela pozycji, podpis."

            invoice_data = self._build_invoice_data(
                invoice_nr, today, parsed, calc, nabywca, sprzedawca, style_info
            )

            # KROK 4: Generowanie faktury
            faktura_text = self._generate_invoice(invoice_data, parsed, calc, invoice_nr, today, nabywca, sprzedawca)

            return {
                "status": "success",
                "parse": parsed,
                "calc": calc,
                "kosztorys_text": kosztorys_text,
                "faktura_text": faktura_text,
                "invoice_nr": invoice_nr,
                "invoice_date": today,
                "error": None,
            }

        except Exception as e:
            logger.error(f"ZlecenieProcessor error: {e}")
            return {"status": "error", "error": str(e)}

    def _build_invoice_data(self, nr, date_str, parsed, calc, nabywca, sprzedawca, style_info) -> str:
        mpp_note = "MECHANIZM PODZIELONEJ PŁATNOŚCI" if calc["mpp_required"] else ""
        return f"""
Numer faktury: {nr}
Data wystawienia: {date_str}
Sprzedawca: {sprzedawca or "[DANE SPRZEDAWCY — uzupełnij: firma, NIP, adres]"}
Nabywca: {nabywca or "[DANE NABYWCY — uzupełnij: firma/osoba, NIP, adres]"}
Pozycja 1: {parsed['typ_pracy'].title()}
  Ilość: {calc['pozycje'][0]['ilosc']} {calc['pozycje'][0]['jednostka']}
  Cena jednostkowa: {calc['cena_m2']} PLN/{calc['jednostka']}
  Wartość netto: {calc['netto']:,.2f} PLN
  Stawka VAT: {calc['vat_rate']}%
  VAT: {calc['vat_kwota']:,.2f} PLN
  Wartość brutto: {calc['brutto']:,.2f} PLN
  w tym materiały netto: {calc['materialy_netto']:,.2f} PLN
  w tym robocizna netto: {calc['robocizna_netto']:,.2f} PLN
Uwagi: {mpp_note}
{style_info}
"""

    def _generate_invoice(self, invoice_data, parsed, calc, invoice_nr, today, nabywca, sprzedawca) -> str:
        """Generuje tekst faktury — AI lub offline template."""
        if self.accountant:
            try:
                result = self.accountant.generate_invoice(invoice_data)
                # Sprawdź czy dostaliśmy prawdziwą fakturę (nie DEMO JSON)
                if "DEMO_MODE" not in result and len(result) > 200:
                    return result
            except Exception:
                pass

        # Offline template — zawsze działa
        return self._offline_invoice_template(invoice_nr, today, parsed, calc, nabywca, sprzedawca)

    def _offline_invoice_template(self, nr, today, parsed, calc, nabywca, sprzedawca) -> str:
        mpp = "\n⚠️  MECHANIZM PODZIELONEJ PŁATNOŚCI" if calc["mpp_required"] else ""
        sprzedawca_txt = sprzedawca or "[TWOJA FIRMA]\n[NIP]\n[ADRES]"
        nabywca_txt = nabywca or "[FIRMA/OSOBA NABYWCA]\n[NIP]\n[ADRES]"

        return f"""
╔══════════════════════════════════════════════════════════╗
║              FAKTURA VAT nr {nr:<28} ║
╚══════════════════════════════════════════════════════════╝

Data wystawienia:  {today}
Miejsce:           Polska

┌────────────────────────┬────────────────────────────────┐
│    SPRZEDAWCA           │    NABYWCA                     │
│{sprzedawca_txt:<24}│{nabywca_txt:<32}│
└────────────────────────┴────────────────────────────────┘

┌──┬──────────────────────────────────┬──────┬──────┬────────────┬────────────┐
│Lp│ Opis (nazwa usługi/towaru)       │  Jed │  Ile │  Cena netto│ Wart.netto │
├──┼──────────────────────────────────┼──────┼──────┼────────────┼────────────┤
│ 1│ {parsed['typ_pracy'].title():<32}│ {calc['jednostka']:<4} │ {calc['pozycje'][0]['ilosc']:<4.0f} │ {calc['cena_m2']:>10.2f} │ {calc['netto']:>10,.2f} │
│  │   w tym: materiały               │      │      │            │ {calc['materialy_netto']:>10,.2f} │
│  │   w tym: robocizna               │      │      │            │ {calc['robocizna_netto']:>10,.2f} │
└──┴──────────────────────────────────┴──────┴──────┴────────────┴────────────┘

┌─────────────────────────────────────────────┐
│  PODSUMOWANIE                               │
│  Wartość netto:           {calc['netto']:>12,.2f} PLN   │
│  VAT {calc['vat_rate']}%:               {calc['vat_kwota']:>12,.2f} PLN   │
│  ┌───────────────────────────────────────┐  │
│  │  DO ZAPŁATY:          {calc['brutto']:>12,.2f} PLN │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
{mpp}

Forma płatności: przelew bankowy 14 dni
Nr konta: [NUMER KONTA BANKOWEGO]

Wystawił: ______________________    Zatwierdził: ______________________
""".strip()
