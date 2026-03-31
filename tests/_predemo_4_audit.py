"""
Test audytu regułowego — weryfikuje nowy _offline_rule_audit
Sprawdza faktury prawidłowe i celowo wadliwą FV_2026_BLAD.txt
"""
import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Block engine loading
from unittest.mock import MagicMock
engine_mock = MagicMock()
engine_mock.generate.return_value = "TRYB DEMONSTRACYJNY (model AI niedostępny)"
engine_mock.get_instance.return_value = engine_mock

import synapsa.engine as _eng_mod
_eng_mod.SynapsaEngine = type('SynapsaEngine', (), {
    'get_instance': staticmethod(lambda: engine_mock),
    'generate': lambda self, p, **kw: "TRYB DEMONSTRACYJNY (model AI niedostępny)"
})()
sys.modules['synapsa.engine'] = _eng_mod

from synapsa.agents.office_agent import SecureAuditAgent

class MockEngine:
    def generate(self, prompt, **kw):
        return "TRYB DEMONSTRACYJNY (model AI niedostępny)"

agent = SecureAuditAgent(engine=MockEngine())

demo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'demo_docs'))

test_files = [
    ("FV_2021_001.txt", ["OK", "OSTRZEZENIA"]),   # stara faktura, brak KSeF ok
    ("FV_2022_007.txt", ["OK", "OSTRZEZENIA"]),   # VAT 8% ocieplenie
    ("FV_2026_001.txt", ["OK", "OSTRZEZENIA"]),   # z KSeF — powinna byc OK
    ("FV_2026_BLAD.txt", ["BLEDY"]),              # wadliwa — MUSI byc BLEDY
]

all_ok = True
print()
print("=" * 65)
print("  TEST AUDYTU REGULOWEGO — SecureAuditAgent (OFFLINE)")
print("=" * 65)

for fname, expected_statuses in test_files:
    fpath = os.path.join(demo_dir, fname)
    if not os.path.exists(fpath):
        print(f"  [XX] {fname} — BRAK PLIKU!")
        all_ok = False
        continue

    result = agent.process_audit("Sprawdź fakturę pod kątem przepisów", [fpath])

    try:
        report = json.loads(result['report'])
    except Exception as e:
        print(f"  [XX] {fname} — Błąd parsowania raportu: {e}")
        all_ok = False
        continue

    status = report.get("status", "?")
    rok = report.get("rok_faktury", "?")
    bledy = report.get("bledy_formalne", [])
    bledy_r = report.get("bledy_rachunkowe", [])
    ostrzezenia = report.get("ostrzezenia", [])
    tryb = report.get("tryb", "?")

    passed = status in expected_statuses
    icon = "OK" if passed else "XX"
    if not passed:
        all_ok = False

    print(f"\n  [{icon}] {fname}")
    print(f"       Rok: {rok} | Status: {status} | Oczekiwano: {expected_statuses}")
    print(f"       Tryb: {tryb}")
    if bledy:
        print(f"       Błędy formalne ({len(bledy)}):")
        for b in bledy:
            print(f"         - {b[:90]}")
    if bledy_r:
        print(f"       Błędy rachunkowe ({len(bledy_r)}):")
        for b in bledy_r:
            print(f"         - {b[:90]}")
    if ostrzezenia:
        print(f"       Ostrzeżenia ({len(ostrzezenia)}):")
        for o in ostrzezenia:
            print(f"         ~ {o[:80]}")
    print(f"       Ocena: {report.get('ocena_ogolna','?')[:100]}")

print()
print("=" * 65)
print("  WYNIK:", "AUDYT REGULOWY DZIALA POPRAWNIE" if all_ok else "BLEDY W AUDYCIE!")
print("=" * 65)
sys.exit(0 if all_ok else 1)
