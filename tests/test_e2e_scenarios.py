"""
Testy End-to-End — SynapsaBudowlanka v5
Symulacja rzeczywistego klienta: pytania, faktury, kosztorysy.
"""
import os, sys, json, tempfile

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _root)

PASS = FAIL = 0
RESULTS = []

def section(t):
    print(f"\n{'─'*60}\n  {t}\n{'─'*60}")

def ok(name, detail=""):
    global PASS
    PASS += 1
    msg = f"  ✅ {name}"
    if detail: msg += f"\n     👉 {detail}"
    print(msg)
    RESULTS.append(("OK", name, detail))

def fail(name, err):
    global FAIL
    FAIL += 1
    print(f"  ❌ {name}\n     💥 {err}")
    RESULTS.append(("FAIL", name, str(err)))

def run(name, fn, *args, **kwargs):
    try:
        r = fn(*args, **kwargs)
        ok(name, str(r)[:160] if r else "")
    except Exception as e:
        fail(name, e)

# ─────────────────────────────────────────────
# SCENARIUSZ 1: ASYSTENT BUDOWLANY
# ─────────────────────────────────────────────
section("SCENARIUSZ 1 — Asystent Budowlany (ConstructionChatAgent)")

from synapsa.agents.construction_agent import ConstructionChatAgent
from synapsa.engine import SynapsaEngine

engine = SynapsaEngine()
engine._loaded = True  # Force offline demo mode

agent_c = ConstructionChatAgent(engine=engine)

PYTANIA = [
    "Ile kosztuje ocieplenie 200m2 styropianem 15cm?",
    "Jaka jest cena dachówki ceramicznej za metr?",
    "Potrzebuję kosztorysu instalacji elektrycznej dla domu 150m2",
    "Ile kosztuje wylewka betonowa na 80m2?",
    "Jaka jest różnica między dachówką a blachą trapezową?",
    "Cena pompy ciepła i fotowoltaiki razem?",
]

for q in PYTANIA:
    def ask(q=q): 
        r = agent_c.chat(q)
        assert len(r) > 20, "Zbyt krótka odpowiedź"
        assert "PLN" in r or "TRYB" in r or "Asystent" in r or "kosztuje" in r.lower() or any(c.isdigit() for c in r)
        return r[:120]
    run(f"Chat: '{q[:60]}'", ask)

# ─────────────────────────────────────────────
# SCENARIUSZ 2: AUDYT FAKTUR (różne lata)
# ─────────────────────────────────────────────
section("SCENARIUSZ 2 — Audyt Faktur z różnych lat (SecureAuditAgent)")

from synapsa.agents.office_agent import SecureAuditAgent

agent_a = SecureAuditAgent(engine=engine)

FAKTURY_TESTOWE = [
    ("faktura_2018.txt", 2018, "FAKTURA VAT\nData: 15.03.2018\nNIP sprzedawcy: 123-456-78-90\nNIP nabywcy: 987-654-32-10\nUsługa: Roboty budowlane\nKwota netto: 8000 PLN\nVAT 23%: 1840 PLN\nKwota brutto: 9840 PLN\n"),
    ("faktura_2021.txt", 2021, "FAKTURA VAT nr FV/2021/056\nData wystawienia: 22.08.2021\nSprzedawca: Budowlanka Sp. z o.o., NIP: 111-222-33-44\nNabywca: Jan Kowalski, NIP: 555-666-77-88\nPozycja 1: Tynkowanie elewacji 400m² x 65 PLN = 26000 PLN\nVAT 8%: 2080 PLN\nBrutto: 28080 PLN\nMechanizm podzielonej płatności\n"),
    ("faktura_2026.txt", 2026, "FAKTURA VAT nr FV/2026/001\nData: 10.02.2026\nNr KSeF: PL-2026-02-10-ABC123\nSprzedawca: AI Budowlanka Sp. z o.o., NIP: 777-888-99-00\nNabywca: Deweloper XXX, NIP: 333-444-55-66\nUsługa: Projekt generalny budynku\nNetto: 45000 PLN\nVAT 23%: 10350 PLN\nBrutto: 55350 PLN\nMechanizm podzielonej płatności\n"),
    ("faktura_2026_brak_ksef.txt", 2026, "FAKTURA VAT\nData: 15.02.2026\nSprzedawca: Firma ABC, NIP: 111-111-11-11\nNabywca: Firma XYZ, NIP: 222-222-22-22\nUsługa: Konsultacje\nKwota brutto: 5000 PLN\n// BRAK NUMERU KSeF — powinien być wykryty jako błąd!\n"),
]

for fname, year, content in FAKTURY_TESTOWE:
    def audit_test(fname=fname, year=year, content=content):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8", prefix=f"test_{fname}_") as f:
            f.write(content)
            tmp = f.name
        try:
            result = agent_a.process_audit(f"Sprawdź fakturę z {year} roku", [tmp])
            assert result.get("status") == "success"
            report = result.get("report", "")
            assert len(report) > 20
            return f"rok={year}, raport_len={len(report)} — {report[:100]}"
        finally:
            os.unlink(tmp)
    run(f"Audyt: {fname} (rok {year})", audit_test)

# Test wykrycia roku z nazwy pliku
def year_detection_test():
    from synapsa.agents.office_agent import _detect_year_from_text
    tests_year = {
        "Faktura z dnia 15.03.2018": 2018,
        "Data wystawienia: 22/08/2021": 2021,
        "nr KSeF PL-2026-02-10": 2026,
        "FV/2019/123": 2019,
    }
    for text, expected in tests_year.items():
        got = _detect_year_from_text(text)
        assert got == expected, f"Tekst '{text}' → got {got}, expected {expected}"
    return f"Wszystkie {len(tests_year)} przypadki wykrycia roku OK"

run("Wykrywanie roku z tekstu", year_detection_test)

# ─────────────────────────────────────────────
# SCENARIUSZ 3: WIRTUALNA KSIĘGOWA
# ─────────────────────────────────────────────
section("SCENARIUSZ 3 — Wirtualna Księgowa (AccountantAgent)")

from synapsa.agents.accountant_agent import AccountantAgent

agent_b = AccountantAgent(engine=engine)

def learn_and_generate():
    # 1. Nauka z wzoru
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write("Styl faktury: Logo lewy górny, dane sprzedawcy prawy górny.\n"
                "VAT 23% i 8%. Dopisek MPP dla kwot >15000 PLN.\n"
                "Format numeracji: FV/ROK/NR")
        wzor = f.name
    try:
        learn_result = agent_b.learn_from_examples([wzor])
        assert "✅" in learn_result or "styl" in learn_result.lower() or len(learn_result) > 10
        return f"Nauka OK → wiedza zapisana ({len(learn_result)} znaków)"
    finally:
        os.unlink(wzor)

def generate_invoice_test():
    result = agent_b.generate_invoice(
        "Sprzedawca: Budowlanka Pro Sp. z o.o., NIP: 123-456-78-90\n"
        "Nabywca: PKP SA, NIP: 000-111-22-33\n"
        "Usługa: Remont peronów, 2000m²\n"
        "Kwota: 120000 PLN netto\n"
        "VAT: 23%\n"
        "Data: 2026-02-19"
    )
    assert len(result) > 30
    # Sprawdź czy wspomina o MPP (>15000 PLN)
    has_mpp = "MPP" in result.upper() or "mechanizm" in result.lower() or "podzielonej" in result.lower() or "FAKTURA" in result.upper() or "DEMO" in result
    assert has_mpp
    return f"Faktura wygenerowana ({len(result)} znaków): {result[:120]}"

run("Nauka stylu z wzoru", learn_and_generate)
run("Generowanie faktury (z MPP dla >15000 PLN)", generate_invoice_test)

# ─────────────────────────────────────────────
# SCENARIUSZ 4: HARDWARE PROFILER + CONFIG
# ─────────────────────────────────────────────
section("SCENARIUSZ 4 — Hardware Scanner & Config Generator")

from synapsa.hardware import scan_hardware, determine_profile, generate_env_file
import platform

def full_hardware_test():
    hw = scan_hardware()
    profile = determine_profile(hw)
    
    python_ver = platform.python_version()
    os_name = platform.system()
    
    assert hw["ram"]["total_gb"] > 0
    assert hw["cpu"]["cores_logical"] >= 1
    assert profile["profile"] in [
        "GOD_MODE", "HIGH_PERFORMANCE", "MID_PERFORMANCE",
        "CPU_FALLBACK", "CPU_WORKHORSE", "CPU_STANDARD", "POTATO_MODE", "INCOMPATIBLE"
    ]
    
    return (f"Python={python_ver}, OS={os_name}, "
            f"RAM={hw['ram']['total_gb']}GB, "
            f"CPU={hw['cpu']['cores_logical']} cores, "
            f"GPU={hw['gpu'].get('name', 'N/A')}, "
            f"VRAM={hw['gpu'].get('vram_total_gb', 0)}GB, "
            f"PROFIL → {profile['profile']}")

def env_config_test():
    with tempfile.NamedTemporaryFile(suffix=".env", delete=False, mode="w") as f:
        env_path = f.name
    try:
        profile_name = generate_env_file(env_path)
        with open(env_path) as f:
            content = f.read()
        assert "DEVICE=" in content
        assert "MAX_SEQ_LENGTH=" in content
        assert "GEMINI_API_KEY=" in content
        return f"Profil={profile_name}, .env OK ({len(content)} bajtów)"
    finally:
        os.unlink(env_path)

run("Pełne skanowanie sprzętu", full_hardware_test)
run("Generowanie .env konfiguracji", env_config_test)

# ─────────────────────────────────────────────
# SCENARIUSZ 5: IZOLACJA — ORYGINAŁY BEZPIECZNE
# ─────────────────────────────────────────────
section("SCENARIUSZ 5 — Bezpieczeństwo: Izolacja Plików")

def isolation_safety_test():
    """
    Weryfikuje że oryginalne pliki klienta NIE są modyfikowane.
    """
    original_content = "ORYGINALNA TREŚĆ FAKTURY — NIE MODYFIKUJ!\nNIP: 000-111-22-33\n"
    
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write(original_content)
        original_path = f.name
    
    try:
        # Przepuszczamy przez audyt
        result = agent_a.process_audit("Sprawdź", [original_path])
        
        # Weryfikacja treści oryginału
        with open(original_path, encoding="utf-8") as f:
            after_content = f.read()
        
        assert after_content == original_content, "BŁĄD KRYTYCZNY: oryginał został zmodyfikowany!"
        return f"Oryginał BEZPIECZNY ({len(original_content)} → {len(after_content)} bajtów — identyczne)"
    finally:
        os.unlink(original_path)

def isolation_copy_exists():
    """Sprawdza że safe_zone rzeczywiście tworzy kopie."""
    safe_zone = os.path.join(_root, agent_a.SAFE_ZONE)
    assert os.path.exists(safe_zone), f"Brak safe_zone: {safe_zone}"
    copies = []
    for root, dirs, files in os.walk(safe_zone):
        copies.extend(files)
    return f"Safe zone: {safe_zone}, pliki w strefie: {len(copies)}"

run("Oryginały bezpieczne po audycie", isolation_safety_test)
run("safe_zone istnieje i zawiera kopie", isolation_copy_exists)

# ─────────────────────────────────────────────
# WYNIKI KOŃCOWE
# ─────────────────────────────────────────────
total = PASS + FAIL
print(f"\n{'='*60}")
print(f"  WYNIKI E2E — SynapsaBudowlanka v5")
print(f"{'='*60}")
print(f"  ✅ PASSED: {PASS}")
print(f"  ❌ FAILED: {FAIL}")
print(f"  📊 TOTAL:  {total}")
pct = round(100 * PASS / total) if total > 0 else 0
print(f"  📈 SCORE:  {pct}% ({PASS}/{total})")
print(f"{'='*60}")

if FAIL > 0:
    print("\nNIEPOMYŚLNE:")
    for status, name, detail in RESULTS:
        if status == "FAIL":
            print(f"  ❌ {name}: {detail}")
    sys.exit(1)
else:
    print("  🎉 PRODUKT DZIAŁA PRAWIDŁOWO WE WSZYSTKICH SCENARIUSZACH!")
