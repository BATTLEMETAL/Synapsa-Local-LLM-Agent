import sys, os
sys.path.insert(0, '.')
from synapsa.agents.zlecenie_processor import ZlecenieParser, ZlecenieCalculator, ZlecenieProcessor

parser = ZlecenieParser()
calc = ZlecenieCalculator()

tests = [
    "mam nowe zlecenie budowanie kostki brukowej, cena 150 za metr kwadratowy, 200m2",
    "ocieplenie elewacji styropianem 15cm, 350m2, stawka 85 zl za m2",
    "wylewka betonowa 80m2, 70 pln za m2",
    "instalacja elektryczna dom 150m2, 20000 pln komplet",
    "brak ceny tylko opis murarstwo",
]

print("\n" + "="*60)
print("  TEST: ZlecenieParser + ZlecenieCalculator")
print("="*60)

for zlecenie in tests:
    p = parser.parse(zlecenie)
    c = calc.calculate(p)
    print(f"\nZLECENIE: {zlecenie[:60]}")
    print(f"  typ={p['typ_pracy']}, m2={p['metraz']}, cena={p['cena_za_m2']}, VAT={p['vat_rate']}%")
    print(f"  netto={c['netto']:,.2f} | VAT={c['vat_kwota']:,.2f} | brutto={c['brutto']:,.2f} | MPP={c['mpp_required']}")
    mat_pct = round(c['materialy_netto'] / c['netto'] * 100) if c['netto'] else 0
    rob_pct = 100 - mat_pct
    print(f"  materialy={c['materialy_netto']:,.2f} ({mat_pct}%) | robocizna={c['robocizna_netto']:,.2f} ({rob_pct}%)")

# Test pelnego pipeline (offline template)
print("\n" + "="*60)
print("  PELNY PIPELINE: kostka brukowa 200m2 @ 150 PLN/m2")
print("="*60)
proc = ZlecenieProcessor(engine=None)
result = proc.process(
    "mam nowe zlecenie budowanie kostki brukowej, cena 150 za metr kwadratowy, 200m2",
    nabywca="Jan Kowalski, NIP: 987-654-32-10",
    sprzedawca="Budowlanka Pro Sp. z o.o., NIP: 123-456-78-90"
)
print(f"\nStatus: {result['status']}")
print(f"Nr faktury: {result.get('invoice_nr')}")
print(f"Data: {result.get('invoice_date')}")
print()
print(result.get('kosztorys_text', ''))
print()
print("--- FAKTURA ---")
print(result.get('faktura_text', ''))
