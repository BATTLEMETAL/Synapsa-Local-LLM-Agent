"""Test 1: Kalkulacje kosztorysowe — tylko parser i kalkulator, bez silnika AI"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from synapsa.agents.zlecenie_processor import ZlecenieParser, ZlecenieCalculator

p = ZlecenieParser()
c = ZlecenieCalculator()

tests = [
    ("kostka brukowa 200m2, cena 150 pln za metr",      30000, 23, 36900, True),
    ("ocieplenie 350m2 styropianem 15cm, 85 zl za m2",  29750,  8, 32130, True),
    ("wylewka betonowa 80m2, 70 pln za m2",              5600, 23,  6888, False),
    ("instalacja elektryczna 20000 pln komplet",         20000, 23, 24600, True),
    ("dach 200m2 dachowka ceramiczna 95 pln za m2",     19000, 23, 23370, True),
    ("ogrodzenie panelowe 100mb, 200 pln za mb",         20000, 23, 24600, True),
]

all_ok = True
print("\n[KALKULACJE KOSZTORYSOWE]")
for txt, en, ev, eb, empp in tests:
    pp = p.parse(txt)
    cc = c.calculate(pp)
    ok = (abs(cc['netto'] - en) < 1 and cc['vat_rate'] == ev and abs(cc['brutto'] - eb) < 1)
    if not ok:
        all_ok = False
    mpp = "MPP" if cc['mpp_required'] else "   "
    status = "OK" if ok else "XX"
    print(f"  [{status}] {mpp} | Netto={cc['netto']:>9,.2f} | VAT {cc['vat_rate']:>2}% | Brutto={cc['brutto']:>9,.2f} | {txt[:45]}")

print()
print("WYNIK:", "WSZYSTKIE KALKULACJE POPRAWNE" if all_ok else "BLEDY KALKULACJI!")
sys.exit(0 if all_ok else 1)
