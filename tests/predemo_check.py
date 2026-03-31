"""
Szybka weryfikacja pre-demo — nie laduje modelu AI, tylko sprawdza
- importy klas
- strukture UI w app_budowlanka.py
- kalkulacje kosztorysowe (tylko logika, bez silnika)
- HTTP ping serwera
"""
import sys, os
# Blokuj ladowanie engine:
# ZlecenieProcessor uzywa lazy loading — ok
# SecureAuditAgent i AccountantAgent laduja SynapsaEngine w __init__
# Pomijamy ich instancjonowanie, tylko sprawdzamy import klasy
sys.path.insert(0, os.path.abspath('.'))

ok = 0
err = 0
lines = []

def chk(name, fn):
    global ok, err
    try:
        result = fn()
        ok += 1
        lines.append(f"  [OK] {name:<50} {result or ''}")
    except Exception as e:
        err += 1
        lines.append(f"  [XX] {name:<50} {str(e)[:80]}")

# ── 1. Importy klas (bez instancjonowania silnika) ──────────────
chk("Import: ZlecenieParser", lambda:
    __import__('synapsa.agents.zlecenie_processor',
               fromlist=['ZlecenieParser']).ZlecenieParser.__name__)

chk("Import: ZlecenieCalculator", lambda:
    __import__('synapsa.agents.zlecenie_processor',
               fromlist=['ZlecenieCalculator']).ZlecenieCalculator.__name__)

chk("Import: ZlecenieProcessor class", lambda:
    __import__('synapsa.agents.zlecenie_processor',
               fromlist=['ZlecenieProcessor']).ZlecenieProcessor.__name__)

chk("Import: ConstructionChatAgent class", lambda:
    __import__('synapsa.agents.construction_agent',
               fromlist=['ConstructionChatAgent']).ConstructionChatAgent.__name__)

chk("Import: SecureAuditAgent class (bez init)", lambda:
    __import__('synapsa.agents.office_agent',
               fromlist=['SecureAuditAgent']).SecureAuditAgent.__name__)

chk("Import: AccountantAgent class (bez init)", lambda:
    __import__('synapsa.agents.accountant_agent',
               fromlist=['AccountantAgent']).AccountantAgent.__name__)

chk("Import: scan_hardware", lambda:
    __import__('synapsa.hardware',
               fromlist=['scan_hardware']).scan_hardware.__name__)

# ── 2. app_budowlanka.py — struktura zakladek i elementow UI ────
with open('app_budowlanka.py', encoding='utf-8') as f:
    src = f.read()

ui_checks = [
    ("Tab: Nowe Zlecenie",           "Nowe Zlecenie"),
    ("Tab: Asystent Budowlany",      "Asystent Budowlany"),
    ("Tab: Audyt Faktur",            "Audyt Faktur"),
    ("Tab: Wirtualna Ksiegowa",      "Wirtualna Ksi"),
    ("Tab: System & Sprzet",         "System"),
    ("UI: text_area zlecenie_text",  "zlecenie_text"),
    ("UI: button Oblicz i wystaw",   "Oblicz i wyst"),
    ("UI: download_button faktury",  "download_button"),
    ("UI: text_input nabywca",       "nabywca"),
    ("UI: text_input sprzedawca",    "sprzedawca"),
    ("UI: Przyklad 1/2/3 buttons",   "Przyk"),
    ("UI: kosztorys metrics display","kosztorys"),
    ("UI: faktura text display",     "faktura"),
    ("UI: session history",          "historia"),
    ("Import ZlecenieProcessor",     "ZlecenieProcessor"),
]
for name, kw in ui_checks:
    chk(name, lambda kw=kw: "OK" if kw in src else (_ for _ in ()).throw(ValueError(f'Brak "{kw}"')))

# ── 3. Kalkulacje kosztorysowe (czysta logika) ─────────────────
from synapsa.agents.zlecenie_processor import ZlecenieParser, ZlecenieCalculator
parser = ZlecenieParser()
calc   = ZlecenieCalculator()

tests = [
    # (opis, text, exp_netto, exp_vat_rate, exp_brutto)
    ("Kostka 200m2 @ 150",         "kostka brukowa 200m2, cena 150 pln za metr",     30000, 23, 36900),
    ("Ocieplenie 350m2 @ 85 VAT8", "ocieplenie 350m2 styropianem 15cm, 85 zl za m2", 29750,  8, 32130),
    ("Wylewka 80m2 @ 70",          "wylewka betonowa 80m2, 70 pln za m2",             5600,  23, 6888),
    ("Instalacja 20k komplet",     "instalacja elektryczna 20000 pln komplet",        20000, 23, 24600),
    ("Dach 200m2 @ 95 MPP",        "dach 200m2 dachowka ceramiczna 95 pln za m2",    19000, 23, 23370),
    ("Ogrodzenie 100mb @ 200",     "ogrodzenie 100mb, 200 pln za mb",                20000, 23, 24600),
]

for name, text, exp_netto, exp_vat, exp_brutto in tests:
    def run(t=text, en=exp_netto, ev=exp_vat, eb=exp_brutto, nm=name):
        p = parser.parse(t)
        c = calc.calculate(p)
        msgs = []
        if abs(c['netto'] - en) > 1:
            msgs.append(f"netto={c['netto']} != {en}")
        if c['vat_rate'] != ev:
            msgs.append(f"vat={c['vat_rate']}% != {ev}%")
        if abs(c['brutto'] - eb) > 1:
            msgs.append(f"brutto={c['brutto']} != {eb}")
        if msgs:
            raise ValueError(", ".join(msgs))
        mpp = " |MPP" if c['mpp_required'] else ""
        return f"Netto={c['netto']:,.0f} | VAT {c['vat_rate']}% | Brutto={c['brutto']:,.0f}{mpp}"
    chk(f"Kalkul: {name}", run)

# ── 4. Format faktury ─────────────────────────────────────────
def chk_fv():
    from synapsa.agents.zlecenie_processor import ZlecenieProcessor
    proc = ZlecenieProcessor()  # lazy — nie laduje silnika
    r = proc.process("budowa ogrodzenia 100mb, 200 pln za mb",
                     sprzedawca="FIRMA DEMO Sp. z o.o.",
                     nabywca="Klient Demo")
    if r['status'] == 'error':
        raise ValueError(r['error'])
    fv = r['faktura_text']
    required = ['FAKTURA VAT', 'DO ZAPŁATY', 'przelew', r['invoice_nr']]
    missing = [k for k in required if k not in fv]
    if missing:
        raise ValueError(f"Brak w fakturze: {missing}")
    return f"{len(fv)} znaków | Nr: {r['invoice_nr']}"

chk("Format TXT faktury (pobierz .txt)", chk_fv)

# ── 5. HTTP ping ───────────────────────────────────────────────
import urllib.request
def ping():
    try:
        r = urllib.request.urlopen('http://localhost:8501', timeout=4)
        return f"HTTP {r.getcode()} OK"
    except Exception as e:
        raise ValueError(str(e))
chk("Streamlit serwer HTTP 200", ping)

# ── 6. Pliki demo ─────────────────────────────────────────────
import glob
demo_files = glob.glob("demo_docs/FV_*.txt")
chk("demo_docs/ — faktury testowe", lambda:
    f"{len(demo_files)} plikow" if len(demo_files) >= 6
    else (_ for _ in ()).throw(ValueError(f"Za malo plikow: {len(demo_files)}")))

# ── RAPORT KONCOWY ────────────────────────────────────────────
print()
print("=" * 65)
print("  RAPORT WERYFIKACJI PRE-DEMO  —  Synapsa Budowlanka v5")
print("=" * 65)
for l in lines:
    print(l)
print()
print(f"  Wynik: {ok}/{ok+err} testow zaliczonych")
print()
fail_lines = [l for l in lines if l.strip().startswith('[XX]')]
if fail_lines:
    print("  BLEDY:")
    for l in fail_lines:
        print(f"   {l.strip()}")
    print()
    verdict = "  STATUS: !! WYMAGA NAPRAWY PRZED PREZENTACJA !!"
else:
    verdict = "  STATUS: GOTOWE DO PREZENTACJI DLA KLIENTA"
print(verdict)
print("=" * 65)
