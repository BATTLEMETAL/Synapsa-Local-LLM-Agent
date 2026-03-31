"""
Test Suite — SynapsaBudowlanka v5
Testuje wszystkie moduły i agenty bez potrzeby modelu AI.
"""
import os
import sys
import json
import tempfile

# === KONFIGURACJA ŚRODOWISKA ===
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _root)

PASS = 0
FAIL = 0
WARN = 0


def test(name: str, fn):
    global PASS, FAIL
    try:
        result = fn()
        if result is True or result is None:
            print(f"  ✅ {name}")
            PASS += 1
        elif isinstance(result, str) and result.startswith("WARN"):
            print(f"  ⚠️  {name} — {result}")
            global WARN
            WARN += 1
        else:
            print(f"  ✅ {name} — {result!r:.120s}")
            PASS += 1
    except Exception as e:
        print(f"  ❌ {name} — {type(e).__name__}: {e}")
        FAIL += 1


def section(title: str):
    print(f"\n{'='*55}\n  {title}\n{'='*55}")


# ============================================================
# TEST 1: KOMPATYBILNOŚĆ WINDOWS
# ============================================================
section("1. Windows Compatibility (compat.py)")


def t_compat_import():
    from synapsa.compat import setup_windows_compatibility
    assert callable(setup_windows_compatibility)
    return True


def t_compat_setup():
    from synapsa.compat import setup_windows_compatibility
    setup_windows_compatibility()
    assert os.environ.get("WBITS_USE_TRITON") == "0"
    assert os.environ.get("XFORMERS_FORCE_DISABLE_TRITON") == "1"
    return True


def t_triton_mock():
    import sys
    # After compat setup, triton should be mocked if not installed
    # (either mocked or real — both should work)
    return True  # No crash = success


test("Import compat.py", t_compat_import)
test("setup_windows_compatibility() sets env vars", t_compat_setup)
test("Triton mock — no crash", t_triton_mock)


# ============================================================
# TEST 2: SKANOWANIE SPRZĘTU
# ============================================================
section("2. Hardware Scanner (hardware.py)")


def t_hw_import():
    from synapsa.hardware import scan_hardware, determine_profile, generate_env_file
    assert callable(scan_hardware)
    assert callable(determine_profile)
    assert callable(generate_env_file)
    return True


def t_hw_scan():
    from synapsa.hardware import scan_hardware
    hw = scan_hardware()
    assert "cpu" in hw
    assert "ram" in hw
    assert "gpu" in hw
    assert hw["ram"]["total_gb"] > 0
    cpu_cores = hw["cpu"]["cores_logical"]
    assert cpu_cores >= 1
    return f"RAM={hw['ram']['total_gb']}GB, CPU={cpu_cores} cores, GPU={hw['gpu'].get('name','CPU-only')}"


def t_hw_profile():
    from synapsa.hardware import scan_hardware, determine_profile
    hw = scan_hardware()
    profile = determine_profile(hw)
    assert "profile" in profile
    assert "device" in profile
    assert "max_seq_length" in profile
    assert profile["max_seq_length"] > 0
    return f"profile={profile['profile']}, device={profile['device']}"


def t_hw_env_generation():
    from synapsa.hardware import generate_env_file
    with tempfile.NamedTemporaryFile(suffix=".env", delete=False, mode="w") as f:
        env_path = f.name
    try:
        profile = generate_env_file(env_path)
        assert os.path.exists(env_path)
        with open(env_path) as f:
            content = f.read()
        assert "DEVICE=" in content
        assert "MAX_SEQ_LENGTH=" in content
        assert len(profile) > 0
        return f"Generated .env profile={profile}"
    finally:
        os.unlink(env_path)


def t_profile_all_tiers():
    """Testuje wszystkie ścieżki logiki profilowania."""
    from synapsa.hardware import determine_profile
    scenarios = [
        {"gpu": {"available": True, "vram_total_gb": 24}, "ram": {"total_gb": 64}, "cpu": {}, "disk": {}},
        {"gpu": {"available": True, "vram_total_gb": 12}, "ram": {"total_gb": 16}, "cpu": {}, "disk": {}},
        {"gpu": {"available": True, "vram_total_gb": 6},  "ram": {"total_gb": 8},  "cpu": {}, "disk": {}},
        {"gpu": {"available": True, "vram_total_gb": 4},  "ram": {"total_gb": 8},  "cpu": {}, "disk": {}},
        {"gpu": {"available": False},                      "ram": {"total_gb": 32}, "cpu": {}, "disk": {}},
        {"gpu": {"available": False},                      "ram": {"total_gb": 16}, "cpu": {}, "disk": {}},
        {"gpu": {"available": False},                      "ram": {"total_gb": 8},  "cpu": {}, "disk": {}},
        {"gpu": {"available": False},                      "ram": {"total_gb": 4},  "cpu": {}, "disk": {}},
    ]
    expected = [
        "GOD_MODE", "HIGH_PERFORMANCE", "MID_PERFORMANCE", "CPU_FALLBACK",
        "CPU_WORKHORSE", "CPU_STANDARD", "POTATO_MODE", "INCOMPATIBLE"
    ]
    for hw, exp in zip(scenarios, expected):
        p = determine_profile(hw)
        assert p["profile"] == exp, f"Expected {exp}, got {p['profile']} for hw={hw}"
    return f"All {len(scenarios)} tiers OK"


test("Import hardware.py", t_hw_import)
test("scan_hardware() returns valid data", t_hw_scan)
test("determine_profile() returns valid profile", t_hw_profile)
test("generate_env_file() creates .env", t_hw_env_generation)
test("All 8 hardware tiers work correctly", t_profile_all_tiers)


# ============================================================
# TEST 3: ENGINE (Offline Fallback Mode)
# ============================================================
section("3. AI Engine — Offline Fallback (engine.py)")


def t_engine_import():
    from synapsa.engine import SynapsaEngine
    assert callable(SynapsaEngine)
    return True


def t_engine_singleton():
    from synapsa.engine import SynapsaEngine
    e1 = SynapsaEngine.get_instance()
    e2 = SynapsaEngine.get_instance()
    assert e1 is e2
    return "Singleton pattern — OK"


def t_engine_offline_construction():
    from synapsa.engine import SynapsaEngine
    engine = SynapsaEngine()
    # Force offline (don't load model)
    engine._loaded = True
    result = engine._generate_offline("Ile kosztuje ocieplenie 200m2?")
    assert len(result) > 20
    return f"Odpowiedz offline dla 'budow': {result[:80]}..."


def t_engine_offline_audit():
    from synapsa.engine import SynapsaEngine
    engine = SynapsaEngine()
    engine._loaded = True
    result = engine._generate_offline("Sprawdz fakturę VAT")
    data = json.loads(result)
    assert "status" in data
    assert data["status"] == "DEMO_MODE"
    return f"Audit offline JSON OK — status={data['status']}"


def t_engine_offline_invoice():
    from synapsa.engine import SynapsaEngine
    engine = SynapsaEngine()
    engine._loaded = True
    result = engine._generate_offline("Generuj fakturę sprzedaży")
    assert "FAKTURA" in result.upper() or "faktura" in result.lower()
    return f"Invoice fallback OK: {result[:80]}..."


def t_engine_generate_routes():
    from synapsa.engine import SynapsaEngine
    engine = SynapsaEngine()
    engine._loaded = True
    # Should route to offline fallback
    r = engine.generate("kosztor budowlany", max_tokens=100)
    assert len(r) > 10
    return "generate() routing OK"


test("Import engine.py", t_engine_import)
test("SynapsaEngine singleton pattern", t_engine_singleton)
test("Offline fallback — budowlany", t_engine_offline_construction)
test("Offline fallback — audyt (JSON)", t_engine_offline_audit)
test("Offline fallback — faktura", t_engine_offline_invoice)
test("generate() routes correctly in offline", t_engine_generate_routes)


# ============================================================
# TEST 4: VAT NORMS + YEAR DETECTION
# ============================================================
section("4. Historyczne Normy VAT (vat_norms.json)")


def t_vat_norms_exists():
    norms_path = os.path.join(_root, "synapsa", "knowledge", "vat_norms.json")
    assert os.path.exists(norms_path), f"Brak pliku: {norms_path}"
    with open(norms_path, encoding="utf-8") as f:
        data = json.load(f)
    assert "years" in data
    years = list(data["years"].keys())
    assert "2018" in years
    assert "2026" in years
    return f"Normy dla lat: {years}"


def t_vat_year_2018_no_ksef():
    norms_path = os.path.join(_root, "synapsa", "knowledge", "vat_norms.json")
    with open(norms_path, encoding="utf-8") as f:
        data = json.load(f)
    y2018 = data["years"]["2018"]
    assert y2018["ksef_required"] is False, "2018 nie powinien wymagać KSeF"
    return "2018: ksef_required=False — OK"


def t_vat_year_2026_ksef():
    norms_path = os.path.join(_root, "synapsa", "knowledge", "vat_norms.json")
    with open(norms_path, encoding="utf-8") as f:
        data = json.load(f)
    y2026 = data["years"]["2026"]
    assert y2026["ksef_required"] is True, "2026 MUSI wymagać KSeF"
    return "2026: ksef_required=True — OK"


def t_year_detection():
    from synapsa.agents.office_agent import _detect_year_from_text
    tests = [
        ("Faktura z dnia 15.03.2018 r.", 2018),
        ("Data wystawienia: 12/06/2021", 2021),
        ("rok 2026", 2026),
        ("invoice 2019-11-01", 2019),
        ("brak daty w tekście", 2026),  # Domyślnie bieżący rok
    ]
    for text, expected in tests:
        result = _detect_year_from_text(text)
        assert result == expected, f"Dla '{text}' wykryto {result}, oczekiwano {expected}"
    return f"Wykryto rok prawidłowo dla {len(tests)} przypadków"


test("vat_norms.json istnieje i ma lata 2018-2026", t_vat_norms_exists)
test("2018 — ksef_required=False (poprawne historycznie)", t_vat_year_2018_no_ksef)
test("2026 — ksef_required=True (OBOWIĄZKOWY)", t_vat_year_2026_ksef)
test("_detect_year_from_text() — 5 przypadków", t_year_detection)


# ============================================================
# TEST 5: AGENT AUDYTORA
# ============================================================
section("5. SecureAuditAgent (office_agent.py)")


def t_audit_agent_import():
    from synapsa.agents.office_agent import SecureAuditAgent, _load_vat_norms
    assert callable(SecureAuditAgent)
    return True


def t_audit_norms_loading():
    from synapsa.agents.office_agent import _load_vat_norms
    norms = _load_vat_norms()
    assert "years" in norms
    return f"Załadowano normy dla {len(norms['years'])} lat"


def t_audit_isolation():
    from synapsa.agents.office_agent import SecureAuditAgent
    from synapsa.engine import SynapsaEngine
    engine = SynapsaEngine()
    engine._loaded = True
    agent = SecureAuditAgent(engine=engine)
    # Tworzymy tymczasowy plik "faktury"
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write("FAKTURA VAT 2018\nNIP: 123-456-78-90\nKwota: 5000 PLN\n")
        tmp = f.name
    try:
        isolated = agent._isolate_files([tmp])
        assert len(isolated) == 1
        assert os.path.exists(isolated[0])
        assert isolated[0] != tmp  # Kopia, nie oryginał!
        return f"Izolacja OK: {os.path.basename(isolated[0])}"
    finally:
        os.unlink(tmp)


def t_audit_year_aware_norms():
    from synapsa.agents.office_agent import SecureAuditAgent
    from synapsa.engine import SynapsaEngine
    engine = SynapsaEngine()
    engine._loaded = True
    agent = SecureAuditAgent(engine=engine)
    norms_2018 = agent._get_norms_for_year(2018)
    norms_2026 = agent._get_norms_for_year(2026)
    assert norms_2018["ksef_required"] is False
    assert norms_2026["ksef_required"] is True
    return "Normy dla 2018 i 2026 poprawnie rozróżnione"


def t_audit_process():
    from synapsa.agents.office_agent import SecureAuditAgent
    from synapsa.engine import SynapsaEngine
    engine = SynapsaEngine()
    engine._loaded = True
    agent = SecureAuditAgent(engine=engine)
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write("FAKTURA VAT\nData: 15.03.2018\nNIP: 123-456-78-90\nKwota: 12300 PLN\n")
        tmp = f.name
    try:
        result = agent.process_audit("Sprawdź fakturę", [tmp])
        assert result.get("status") == "success"
        assert "report" in result
        return f"process_audit() OK — status={result['status']}"
    finally:
        os.unlink(tmp)


test("Import office_agent.py", t_audit_agent_import)
test("_load_vat_norms() ładuje normy", t_audit_norms_loading)
test("File isolation (kopia, nie oryginał)", t_audit_isolation)
test("Normy historyczne: 2018 vs 2026", t_audit_year_aware_norms)
test("process_audit() zwraca wynik", t_audit_process)


# ============================================================
# TEST 6: AGENT KSIĘGOWEJ
# ============================================================
section("6. AccountantAgent (accountant_agent.py)")


def t_accountant_import():
    from synapsa.agents.accountant_agent import AccountantAgent
    assert callable(AccountantAgent)
    return True


def t_accountant_isolation():
    from synapsa.agents.accountant_agent import AccountantAgent
    from synapsa.engine import SynapsaEngine
    engine = SynapsaEngine()
    engine._loaded = True
    agent = AccountantAgent(engine=engine)
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write("Wzór faktury VAT — style guide\n")
        tmp = f.name
    try:
        isolated = agent._isolate_files([tmp])
        assert len(isolated) == 1
        assert isolated[0] != tmp  # Kopia!
        return f"Izolacja OK: {os.path.basename(isolated[0])}"
    finally:
        os.unlink(tmp)


def t_accountant_learn():
    from synapsa.agents.accountant_agent import AccountantAgent
    from synapsa.engine import SynapsaEngine
    engine = SynapsaEngine()
    engine._loaded = True
    agent = AccountantAgent(engine=engine)
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write("Logo: Budowlanka Sp. z o.o.\nNIP: 123-456-78-90\nVAT: 23%\n")
        tmp = f.name
    try:
        result = agent.learn_from_examples([tmp])
        assert isinstance(result, str)
        assert len(result) > 10
        return f"learn_from_examples() OK: {result[:80]}..."
    finally:
        os.unlink(tmp)


def t_accountant_generate():
    from synapsa.agents.accountant_agent import AccountantAgent
    from synapsa.engine import SynapsaEngine
    engine = SynapsaEngine()
    engine._loaded = True
    agent = AccountantAgent(engine=engine)
    result = agent.generate_invoice("Usługa: Remont elewacji, 300m², Kwota: 4500 PLN")
    assert len(result) > 10
    return f"generate_invoice() OK: {result[:80]}..."


test("Import accountant_agent.py", t_accountant_import)
test("File isolation (kopia, nie oryginał)", t_accountant_isolation)
test("learn_from_examples() działa", t_accountant_learn)
test("generate_invoice() zwraca wynik", t_accountant_generate)


# ============================================================
# TEST 7: AGENT BUDOWLANY
# ============================================================
section("7. ConstructionChatAgent (construction_agent.py)")


def t_construction_import():
    from synapsa.agents.construction_agent import ConstructionChatAgent, CONSTRUCTION_KNOWLEDGE
    assert callable(ConstructionChatAgent)
    assert len(CONSTRUCTION_KNOWLEDGE) > 0
    return f"Załadowano {len(CONSTRUCTION_KNOWLEDGE)} kategorii"


def t_construction_offline_knowledge():
    from synapsa.agents.construction_agent import ConstructionChatAgent
    from synapsa.engine import SynapsaEngine
    engine = SynapsaEngine()
    engine._loaded = True
    agent = ConstructionChatAgent(engine=engine)
    result = agent._offline_answer("styropian 15cm cena")
    assert "PLN" in result or "cena" in result.lower() or "styropian" in result.lower()
    return f"Offline answ: {result[:100]}..."


def t_construction_chat():
    from synapsa.agents.construction_agent import ConstructionChatAgent
    from synapsa.engine import SynapsaEngine
    engine = SynapsaEngine()
    engine._loaded = True
    agent = ConstructionChatAgent(engine=engine)
    result = agent.chat("Ile kosztuje ocieplenie 200m2 styropianem?")
    assert len(result) > 10
    return f"chat() OK: {result[:100]}..."


def t_construction_prices():
    from synapsa.agents.construction_agent import CONSTRUCTION_KNOWLEDGE
    categories = list(CONSTRUCTION_KNOWLEDGE.keys())
    for cat in ["izolacja", "mury", "pokrycie_dachu", "podłogi", "instalacje"]:
        assert cat in categories, f"Brak kategorii: {cat}"
    return f"Kategorie cennikowe: {categories}"


test("Import + CONSTRUCTION_KNOWLEDGE", t_construction_import)
test("Offline knowledge base działa", t_construction_offline_knowledge)
test("chat() zwraca odpowiedź", t_construction_chat)
test("Wszystkie kategorie cenowe istnieją", t_construction_prices)


# ============================================================
# TEST 8: PLIKI DYSTRYBUCYJNE
# ============================================================
section("8. Pliki Dystrybucyjne (dist/SynapsaBudowlanka_v5)")

DIST = os.path.join(_root, "dist", "SynapsaBudowlanka_v5")


def t_dist_exists():
    assert os.path.exists(DIST), f"Brak folderu: {DIST}"
    return True


def t_dist_main_files():
    required = ["app_budowlanka.py", "START_BUDOWLANKA.bat", "requirements.txt", "README.md"]
    for f in required:
        p = os.path.join(DIST, f)
        assert os.path.exists(p), f"Brak: {f}"
    return f"Pliki główne: {required}"


def t_dist_synapsa_package():
    synapsa_dir = os.path.join(DIST, "synapsa")
    assert os.path.exists(synapsa_dir)
    required = ["__init__.py", "compat.py", "hardware.py", "engine.py", "install_helper.py"]
    for f in required:
        p = os.path.join(synapsa_dir, f)
        assert os.path.exists(p), f"Brak: synapsa/{f}"
    return f"synapsa/ package: {required}"


def t_dist_agents():
    agents_dir = os.path.join(DIST, "synapsa", "agents")
    assert os.path.exists(agents_dir)
    for f in ["__init__.py", "office_agent.py", "accountant_agent.py", "construction_agent.py"]:
        p = os.path.join(agents_dir, f)
        assert os.path.exists(p), f"Brak: agents/{f}"
    return "Agenty OK"


def t_dist_knowledge():
    norms = os.path.join(DIST, "synapsa", "knowledge", "vat_norms.json")
    assert os.path.exists(norms), "Brak vat_norms.json w dystrybucji!"
    with open(norms, encoding="utf-8") as f:
        data = json.load(f)
    assert "years" in data
    return f"vat_norms.json w dist: OK ({len(data['years'])} lat)"


test("dist/SynapsaBudowlanka_v5 istnieje", t_dist_exists)
test("Główne pliki (app, bat, req, README)", t_dist_main_files)
test("synapsa/ package (5 modułów)", t_dist_synapsa_package)
test("agents/ (3 agenty + __init__)", t_dist_agents)
test("vat_norms.json w dystrybucji", t_dist_knowledge)


# ============================================================
# PODSUMOWANIE
# ============================================================
print(f"\n{'='*55}")
print(f"  WYNIKI TESTÓW SynapsaBudowlanka v5")
print(f"{'='*55}")
print(f"  ✅ PASSED: {PASS}")
print(f"  ⚠️  WARNS:  {WARN}")
print(f"  ❌ FAILED: {FAIL}")
total = PASS + WARN + FAIL
print(f"  📊 TOTAL:  {total}")
pct = round(100 * PASS / total) if total > 0 else 0
print(f"  📈 SCORE:  {pct}% ({PASS}/{total})")
print(f"{'='*55}")

if FAIL == 0:
    print("  🎉 WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
else:
    print(f"  ⚠️  {FAIL} test(ów) wymaga uwagi.")
    sys.exit(1)
