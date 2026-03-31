"""
Generator testowych faktur VAT dla firmy budowlanej.
Tworzy realistyczne faktury z różnych lat do testowania:
- Wirtualnej Księgowej (nauka stylu)
- Audytora (weryfikacja historycznych norm VAT)
- Pipelinu ZlecenieProcessor (porównanie ze wzorcem)
"""
import os, json
from datetime import date

# Folder wyjściowy
OUT_DIR = "demo_docs"
os.makedirs(OUT_DIR, exist_ok=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DANE FIRMOWE (sprzedawca — Twoja firma budowlana)
SPRZEDAWCA = {
    "nazwa": "BUDOWLANKA PRO Sp. z o.o.",
    "nip": "123-456-78-90",
    "adres": "ul. Budowlana 15, 00-001 Warszawa",
    "tel": "+48 600 100 200",
    "email": "biuro@budowlankapro.pl",
    "konto": "PL61 1090 1014 0000 0712 1981 2345",
    "bank": "Bank Pekao S.A.",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KILENT (nabywcy — różne firmy/osoby)
KLIENCI = [
    {"nazwa": "JAN KOWALSKI", "nip": "987-654-32-10", "adres": "ul. Kwiatowa 5, 01-234 Kraków"},
    {"nazwa": "FIRMA BUDOWLANA ABC Sp. z o.o.", "nip": "111-222-33-44", "adres": "ul. Prosta 10, 50-001 Wrocław"},
    {"nazwa": "WSPÓLNOTA MIESZKANIOWA SŁONECZNA 12", "nip": "---", "adres": "ul. Słoneczna 12, 30-001 Poznań"},
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEFINICJE FAKTUR TESTOWYCH
FAKTURY = [
    # --- 2021: Sprzed KSeF, MPP dla > 15000 ---
    {
        "nr": "FV/2021/001",
        "data": "15.03.2021",
        "termin": "29.03.2021",
        "nabywca": KLIENCI[0],
        "pozycje": [
            {"opis": "Układanie kostki brukowej — 250 m²", "jed": "m²", "ile": 250, "cena_netto": 120.0, "vat": 23},
        ],
        "uwagi": "Mechanizm podzielonej płatności",
        "rok_uwagi": "2021 — split payment od 15 000 PLN",
    },
    # --- 2022: Standardowa faktura, ocieplenie z VAT 8% ---
    {
        "nr": "FV/2022/007",
        "data": "10.06.2022",
        "termin": "24.06.2022",
        "nabywca": KLIENCI[2],
        "pozycje": [
            {"opis": "Ocieplenie elewacji styropianem 15cm — 180 m²", "jed": "m²", "ile": 180, "cena_netto": 75.0, "vat": 8},
            {"opis": "Tynk elewacyjny silikonowy — 180 m²", "jed": "m²", "ile": 180, "cena_netto": 45.0, "vat": 8},
        ],
        "uwagi": "",
        "rok_uwagi": "2022 — bez KSeF, VAT 8% dla budownictwa mieszkaniowego",
    },
    # --- 2023: Dach pełna robocizna z materiałami ---
    {
        "nr": "FV/2023/015",
        "data": "20.08.2023",
        "termin": "03.09.2023",
        "nabywca": KLIENCI[1],
        "pozycje": [
            {"opis": "Pokrycie dachu dachówką ceramiczną — 220 m²", "jed": "m²", "ile": 220, "cena_netto": 95.0, "vat": 23},
            {"opis": "Montaż rynien i obróbki blacharskie — komplet", "jed": "kpl", "ile": 1, "cena_netto": 3500.0, "vat": 23},
        ],
        "uwagi": "Mechanizm podzielonej płatności",
        "rok_uwagi": "2023 — bez KSeF (dobrowolny dla dużych firm od 2024)",
    },
    # --- 2026: Z numerem KSeF, aktualne przepisy ---
    {
        "nr": "FV/2026/001",
        "data": "20.02.2026",
        "termin": "06.03.2026",
        "nabywca": KLIENCI[0],
        "pozycje": [
            {"opis": "Wylewka betonowa podłogowa — 120 m²", "jed": "m²", "ile": 120, "cena_netto": 85.0, "vat": 23},
        ],
        "ksef_nr": "PL FA 2026 02200001234567890",
        "uwagi": "",
        "rok_uwagi": "2026 — KSeF OBOWIĄZKOWY, numer KSeF w fakturze",
    },
    # --- 2026: Duże zlecenie, MPP + KSeF ---
    {
        "nr": "FV/2026/002",
        "data": "20.02.2026",
        "termin": "06.03.2026",
        "nabywca": KLIENCI[1],
        "pozycje": [
            {"opis": "Budowa parkingu kostka brukowa — 500 m²", "jed": "m²", "ile": 500, "cena_netto": 150.0, "vat": 23},
            {"opis": "Krawężniki betonowe montaż — 120 mb", "jed": "mb", "ile": 120, "cena_netto": 35.0, "vat": 23},
        ],
        "ksef_nr": "PL FA 2026 02200001234567891",
        "uwagi": "Mechanizm podzielonej płatności",
        "rok_uwagi": "2026 — KSeF + MPP (kwota > 15 000 PLN)",
    },
    # --- WADLIWA faktura do audytu (celowe błędy) ---
    {
        "nr": "FV/2026/BLAD",
        "data": "20.02.2026",
        "termin": "",  # brak terminu
        "nabywca": {"nazwa": "Klient Testowy", "nip": "???", "adres": ""},  # błędny NIP, brak adresu
        "pozycje": [
            {"opis": "Usługa remontowa", "jed": "kpl", "ile": 1, "cena_netto": 20000.0, "vat": 7},  # błędna stawka VAT!
        ],
        "uwagi": "",  # BRAK MPP mimo kwoty > 15000!
        "rok_uwagi": "2026 — FAKTURA Z BŁĘDAMI: brak terminu, błędny NIP, stawka VAT 7% (nie istnieje), brak MPP",
        "_wadliwa": True,
    },
]


def oblicz_pozycje(pozycje):
    """Oblicza sumy dla pozycji faktury."""
    total_netto = 0
    total_vat = 0
    for p in pozycje:
        netto = p["ile"] * p["cena_netto"]
        vat_kwota = round(netto * p["vat"] / 100, 2)
        p["netto"] = round(netto, 2)
        p["vat_kwota"] = vat_kwota
        p["brutto"] = round(netto + vat_kwota, 2)
        total_netto += netto
        total_vat += vat_kwota
    total_brutto = round(total_netto + total_vat, 2)
    return total_netto, total_vat, total_brutto


def generuj_fakture_txt(f):
    """Generuje realistyczny tekst faktury."""
    pozycje = f["pozycje"]
    total_netto, total_vat, total_brutto = oblicz_pozycje(pozycje)
    mpp = f.get("uwagi", "")
    ksef = f.get("ksef_nr", "")
    nabywca = f["nabywca"]
    
    # Grupuj VAT
    vat_summary = {}
    for p in pozycje:
        key = p["vat"]
        vat_summary.setdefault(key, {"netto": 0, "vat": 0})
        vat_summary[key]["netto"] += p["netto"]
        vat_summary[key]["vat"] += p["vat_kwota"]
    
    lines = [
        "=" * 70,
        f"  FAKTURA VAT  nr {f['nr']}",
        "=" * 70,
        "",
    ]
    if ksef:
        lines += [f"  Numer KSeF: {ksef}", ""]
    
    lines += [
        f"  Data wystawienia:   {f['data']}",
        f"  Data sprzedaży:     {f['data']}",
    ]
    if f.get("termin"):
        lines.append(f"  Termin płatności:   {f['termin']}")
    lines.append(f"  Forma płatności:    przelew bankowy")
    lines.append("")
    lines += [
        f"  SPRZEDAWCA:",
        f"  {SPRZEDAWCA['nazwa']}",
        f"  NIP: {SPRZEDAWCA['nip']}",
        f"  {SPRZEDAWCA['adres']}",
        f"  Tel: {SPRZEDAWCA['tel']}  |  E-mail: {SPRZEDAWCA['email']}",
        "",
        f"  NABYWCA:",
        f"  {nabywca['nazwa']}",
        f"  NIP: {nabywca['nip']}",
        f"  {nabywca['adres']}",
        "",
        "-" * 70,
        f"  {'Lp':>2}  {'Opis usługi/towaru':<35}  {'Jed':>4}  {'Ile':>6}  {'Cena':>8}  {'Netto':>10}  {'VAT%':>5}  {'Brutto':>10}",
        "-" * 70,
    ]
    
    for i, p in enumerate(pozycje, 1):
        lines.append(
            f"  {i:>2}  {p['opis']:<35}  {p['jed']:>4}  {p['ile']:>6.1f}  {p['cena_netto']:>8.2f}  {p['netto']:>10,.2f}  {p['vat']:>4}%  {p['brutto']:>10,.2f}"
        )
    
    lines += [
        "-" * 70,
        "",
        f"  PODSUMOWANIE:",
        f"  Wartość netto:             {total_netto:>12,.2f} PLN",
    ]
    for vat_rate, vals in sorted(vat_summary.items()):
        lines.append(f"  VAT {vat_rate}% (netto {vals['netto']:,.2f}):  {vals['vat']:>12,.2f} PLN")
    lines += [
        f"  ─────────────────────────────────────────────",
        f"  DO ZAPŁATY:                {total_brutto:>12,.2f} PLN",
        f"  ═════════════════════════════════════════════",
        "",
    ]
    if mpp:
        lines += [f"  *** {mpp} ***", ""]
    lines += [
        f"  Nr konta:  {SPRZEDAWCA['konto']}",
        f"  Bank:      {SPRZEDAWCA['bank']}",
        f"  Tytuł przelewu: {f['nr']}",
        "",
        f"  Uwagi: {f.get('rok_uwagi', '')}",
        "",
        "  Wystawił: ___________________________   Zatwierdził: ___________________________",
        "",
        "=" * 70,
    ]
    return "\n".join(lines), total_netto, total_vat, total_brutto


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GENEROWANIE PLIKÓW
generated = []
print("\n📄 GENEROWANIE TESTOWYCH FAKTUR VAT\n" + "="*50)
for f in FAKTURY:
    txt, netto, vat_kwota, brutto = generuj_fakture_txt(f)
    
    filename = f['nr'].replace('/', '_') + ".txt"
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(txt)
    
    wadliwa = "⚠️ WADLIWA" if f.get("_wadliwa") else "✅ OK"
    print(f"  {wadliwa}  {f['nr']:<22} | Brutto: {brutto:>10,.2f} PLN | {f['data']}")
    generated.append({"nr": f["nr"], "path": path, "brutto": brutto, "data": f["data"], "wadliwa": f.get("_wadliwa", False)})

# Zapisz manifest
manifest_path = os.path.join(OUT_DIR, "_manifest.json")
with open(manifest_path, "w", encoding="utf-8") as fp:
    json.dump({"faktury": generated, "sprzedawca": SPRZEDAWCA}, fp, indent=2, ensure_ascii=False)

print(f"\n✅ Wygenerowano {len(generated)} faktur w folderze '{OUT_DIR}/'")
print(f"   Manifest: {manifest_path}")
