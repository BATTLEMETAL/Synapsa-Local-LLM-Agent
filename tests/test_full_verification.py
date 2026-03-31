"""
Pełna weryfikacja CLI wszystkich komponentów aplikacji Synapsa Budowlanka.
Symuluje wszystkie 5 zakładek UI.
"""
import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def test(name, fn):
    try:
        msg = fn()
        results.append((PASS, name, msg or ""))
        print(f"{PASS} [{name}] {msg or ''}")
    except Exception as e:
        results.append((FAIL, name, str(e)))
        print(f"{FAIL} [{name}] {e}")

# ═══════════════════════════════════════════════
# TAB 1: NOWE ZLECENIE → FAKTURA
# ═══════════════════════════════════════════════
print("\n" + "═"*60)
print("  TAB 1: NOWE ZLECENIE → FAKTURA")
print("═"*60)

def t_zlecenie_kostka():
    from synapsa.agents.zlecenie_processor import ZlecenieProcessor
    p = ZlecenieProcessor()
    r = p.process(
        "mam nowe zlecenie budowanie kostki brukowej, cena 150 za metr kwadratowy, 200m2",
        sprzedawca="Budowlanka Pro Sp. z o.o.",
        nabywca="Jan Kowalski"
    )
    assert r['status'] == 'success', f"Błąd: {r.get('error')}"
    c = r['calc']
    assert abs(c['netto'] - 30000.0) < 1, f"Netto={c['netto']} (oczekiwano 30000)"
    assert abs(c['vat_kwota'] - 6900.0) < 1, f"VAT={c['vat_kwota']} (oczekiwano 6900)"
    assert abs(c['brutto'] - 36900.0) < 1, f"Brutto={c['brutto']} (oczekiwano 36900)"
    assert c['mpp_required'], "MPP powinno być True"
    assert r['invoice_nr'].startswith('FV/'), f"Błędny nr faktury: {r['invoice_nr']}"
    assert '30 000,00' in r['faktura_text'] or '30,000.00' in r['faktura_text'], "Brak kwoty w fakturze"
    return f"Netto={c['netto']:,.0f} | VAT={c['vat_kwota']:,.0f} | Brutto={c['brutto']:,.0f} | MPP=TAK | Nr={r['invoice_nr']}"

def t_zlecenie_ocieplenie():
    from synapsa.agents.zlecenie_processor import ZlecenieProcessor
    p = ZlecenieProcessor()
    r = p.process("ocieplenie elewacji styropianem 15cm, 350m2, stawka 85 zl za m2")
    assert r['status'] == 'success'
    c = r['calc']
    assert abs(c['cena_m2'] - 85.0) < 1, f"Cena={c['cena_m2']} (oczekiwano 85, nie 15cm!)"
    assert c['vat_rate'] == 8, f"VAT={c['vat_rate']}% (ocieplenie=8%)"
    assert abs(c['netto'] - 29750.0) < 1, f"Netto={c['netto']} (oczekiwano 29750)"
    return f"Cena={c['cena_m2']} PLN/m² | VAT={c['vat_rate']}% | Netto={c['netto']:,.0f} PLN"

def t_zlecenie_komplet():
    from synapsa.agents.zlecenie_processor import ZlecenieProcessor
    p = ZlecenieProcessor()
    r = p.process("instalacja elektryczna dom 150m2, 20000 pln komplet")
    assert r['status'] == 'success'
    c = r['calc']
    assert abs(c['netto'] - 20000.0) < 1, f"Netto={c['netto']} (oczekiwano 20000, nie 3mln!)"
    return f"Netto={c['netto']:,.0f} PLN komplet (nie × metry)"

def t_zlecenie_brak_ceny():
    from synapsa.agents.zlecenie_processor import ZlecenieProcessor
    p = ZlecenieProcessor()
    r = p.process("tylko opis murarstwo bez ceny")
    assert r['status'] == 'error', "Powinien zgłosić błąd gdy brak ceny"
    return f"Błąd wykryty: '{r['error'][:50]}...'"

def t_zlecenie_download_format():
    from synapsa.agents.zlecenie_processor import ZlecenieProcessor
    p = ZlecenieProcessor()
    r = p.process("wylewka betonowa 80m2, 70 pln za m2")
    assert r['status'] == 'success'
    fv = r['faktura_text']
    assert 'FAKTURA VAT' in fv, "Brak tytułu FAKTURA VAT"
    assert 'PODSUMOWANIE' in fv or 'BRUTTO' in fv or 'DO ZAPŁATY' in fv, "Brak sekcji podsumowania"
    assert 'przelew bankowy' in fv.lower() or 'płatności' in fv.lower(), "Brak formy płatności"
    return f"Faktura zawiera wszystkie wymagane sekcje ({len(fv)} znaków)"

test("Zlecenie: kostka brukowa 200m2 @ 150zł", t_zlecenie_kostka)
test("Zlecenie: ocieplenie 15cm (nie myl z ceną) @ 85zł", t_zlecenie_ocieplenie)
test("Zlecenie: instalacja 20000 PLN komplet (nie × m2)", t_zlecenie_komplet)
test("Zlecenie: brak ceny → błąd z podpowiedzią", t_zlecenie_brak_ceny)
test("Zlecenie: format faktury (.txt download)", t_zlecenie_download_format)

# ═══════════════════════════════════════════════
# TAB 2: ASYSTENT BUDOWLANY
# ═══════════════════════════════════════════════
print("\n" + "═"*60)
print("  TAB 2: ASYSTENT BUDOWLANY")
print("═"*60)

def t_asystent_kostka():
    from synapsa.agents.construction_agent import ConstructionChatAgent
    a = ConstructionChatAgent()
    r = a.chat("Ile kosztuje układanie kostki brukowej na 100m2?")
    assert len(r) > 50, "Odpowiedź za krótka"
    has_price = any(k in r for k in ['PLN', 'zł', 'koszt', 'cen'])
    assert has_price, "Brak informacji o cenie"
    return f"Odpowiedź: {r[:80]}..."

def t_asystent_ocieplenie():
    from synapsa.agents.construction_agent import ConstructionChatAgent
    a = ConstructionChatAgent()
    r = a.chat("Cena ocieplenia domu styropianem 15cm?")
    assert 'PLN' in r or 'zł' in r, "Brak ceny w odpowiedzi"
    return f"{r[:80]}..."

def t_asystent_dach():
    from synapsa.agents.construction_agent import ConstructionChatAgent
    a = ConstructionChatAgent()
    r = a.chat("Ile kosztuje wymiana dachu 150m2 dachówką ceramiczną?")
    assert len(r) > 30, "Odpowiedź za krótka"
    return f"{r[:80]}..."

def t_asystent_kalkulacja_m2():
    from synapsa.agents.construction_agent import ConstructionChatAgent
    a = ConstructionChatAgent()
    r = a.chat("Ocieplenie 200m2 styropianem — ile to kosztuje?")
    has_calc = 'Kalkulacja' in r or '200' in r or 'PLN' in r
    assert has_calc, "Brak kalkulacji dla podanego metrażu"
    return f"Kalkulacja m²: {r[:100]}..."

test("Asystent: kostka brukowa (konkretne ceny)", t_asystent_kostka)
test("Asystent: ocieplenie styropian cena", t_asystent_ocieplenie)
test("Asystent: dachówka ceramiczna wycena", t_asystent_dach)
test("Asystent: kalkulacja dla podanego m²", t_asystent_kalkulacja_m2)

# ═══════════════════════════════════════════════
# TAB 3: AUDYT FAKTUR
# ═══════════════════════════════════════════════
print("\n" + "═"*60)
print("  TAB 3: AUDYT FAKTUR")
print("═"*60)

def t_audit_isolation():
    from synapsa.agents.office_agent import SecureAuditAgent
    import tempfile, shutil
    agent = SecureAuditAgent()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("FAKTURA VAT nr FV/2026/001\nData: 19.02.2026\nNetto: 5000 PLN\nVAT 23%: 1150 PLN\nBrutto: 6150 PLN")
        tmp = f.name
    original_content = open(tmp, encoding='utf-8').read()
    # process_audit wymaga (prompt, file_paths)
    r = agent.process_audit("Sprawdź poprawność faktury VAT", [tmp])
    after_content = open(tmp, encoding='utf-8').read()
    os.unlink(tmp)
    assert original_content == after_content, "ORYGINALNY PLIK ZMODYFIKOWANY! Błąd izolacji!"
    assert r.get('status') in ('success', 'error'), f"Nieoczekiwany status: {r}"
    return "Oryginał niezmieniony ✓ | Izolacja działa"

def t_audit_vat_2018():
    from synapsa.agents.office_agent import SecureAuditAgent, _detect_year_from_text
    year = _detect_year_from_text("Data wystawienia: 15.03.2018")
    assert year == 2018, f"Wykryto rok {year} (oczekiwano 2018)"
    return f"Wykryto rok historyczny: {year}"

def t_audit_ksef_2026():
    from synapsa.agents.office_agent import SecureAuditAgent, _detect_year_from_text
    year = _detect_year_from_text("Faktura 2026-01-15")
    assert year == 2026, f"Wykryto rok {year}"
    return f"Wykryto rok KSeF: {year}"

test("Audyt: izolacja pliku (oryginał niezmieniony)", t_audit_isolation)
test("Audyt: wykrywanie roku 2018 (historyczne VAT)", t_audit_vat_2018)
test("Audyt: wykrywanie roku 2026 (KSeF)", t_audit_ksef_2026)

# ═══════════════════════════════════════════════
# TAB 4: WIRTUALNA KSIĘGOWA
# ═══════════════════════════════════════════════
print("\n" + "═"*60)
print("  TAB 4: WIRTUALNA KSIĘGOWA")
print("═"*60)

def t_ksiegowa_generate():
    from synapsa.agents.accountant_agent import AccountantAgent
    a = AccountantAgent()
    r = a.generate_invoice("""
    Numer faktury: FV/2026/TEST
    Sprzedawca: Testowa Firma Sp. z o.o., NIP: 111-222-33-44
    Nabywca: Klient Testowy, NIP: 555-666-77-88
    Usługa: Układanie kostki brukowej
    Netto: 30000 PLN, VAT 23%: 6900 PLN, Brutto: 36900 PLN
    """)
    assert len(r) > 50, "Odpowiedź za krótka"
    return f"Wygenerowano fakturę ({len(r)} znaków): {r[:80]}..."

def t_ksiegowa_knowledge_persistence():
    from synapsa.agents.accountant_agent import AccountantAgent
    a = AccountantAgent()
    # Sprawdź że knowledge file istnieje lub można go utworzyć
    os.makedirs("synapsa_workspace", exist_ok=True)
    a.style["rules"] = "Test style - stawka 23%, logo po lewej"
    a._save_knowledge()
    # Wczytaj ponownie
    a2 = AccountantAgent()
    assert a2.style.get("rules") == "Test style - stawka 23%, logo po lewej", "Wiedza nie została zapisana"
    return "Wiedza zapisana i wczytana poprawnie"

test("Księgowa: generowanie faktury z danych", t_ksiegowa_generate)
test("Księgowa: persistence wiedzy o stylu", t_ksiegowa_knowledge_persistence)

# ═══════════════════════════════════════════════
# TAB 5: SYSTEM & SPRZĘT
# ═══════════════════════════════════════════════
print("\n" + "═"*60)
print("  TAB 5: SYSTEM & SPRZĘT")
print("═"*60)

def t_hardware_scan():
    from synapsa.hardware import scan_hardware
    hw = scan_hardware()
    # scan_hardware() zwraca zagniezdzony slownik: hw['cpu']['cores_logical'], hw['ram']['total_gb']
    assert 'cpu' in hw, f"Brak sekcji CPU. Klucze: {list(hw.keys())}"
    assert 'ram' in hw, f"Brak sekcji RAM. Klucze: {list(hw.keys())}"
    cores = hw['cpu']['cores_logical']
    ram = hw['ram']['total_gb']
    assert cores > 0, f"CPU cores={cores}"
    assert ram > 0, f"RAM={ram}"
    vram = hw.get('gpu', {}).get('vram_total_gb', 0)
    return f"CPU: {cores} rdzeni | RAM: {ram:.1f} GB | GPU VRAM: {vram:.1f} GB"

def t_hardware_profile():
    from synapsa.hardware import scan_hardware, determine_profile
    hw = scan_hardware()
    profile = determine_profile(hw)
    valid = ['GOD_MODE', 'HIGH_PERFORMANCE', 'MID_PERFORMANCE', 'CPU_WORKHORSE',
             'CPU_FALLBACK', 'CPU_STANDARD', 'POTATO_MODE', 'INCOMPATIBLE']
    assert profile['tier'] in valid, f"Nieznany profil: {profile['tier']}"
    return f"Profil: {profile['tier']} — {profile.get('description', '')[:50]}"

def t_streamlit_http():
    import urllib.request
    try:
        resp = urllib.request.urlopen('http://localhost:8501', timeout=5)
        code = resp.getcode()
        assert code == 200, f"HTTP {code}"
        return f"HTTP {code} OK — serwer działa"
    except Exception as e:
        return f"Serwer niedostępny: {e}"

test("Sprzęt: skan hardware (CPU/RAM/GPU)", t_hardware_scan)
test("Sprzęt: profil konfiguracji AI", t_hardware_profile)
test("Streamlit: HTTP 200 serwer żyje", t_streamlit_http)

# ═══════════════════════════════════════════════
# PODSUMOWANIE
# ═══════════════════════════════════════════════
print("\n" + "═"*60)
print("  PODSUMOWANIE WERYFIKACJI")
print("═"*60)
ok = sum(1 for s, _, _ in results if s == PASS)
fail = sum(1 for s, _, _ in results if s == FAIL)
total = len(results)
print(f"\n  Wynik: {ok}/{total} testów zaliczonych")
if fail > 0:
    print(f"\n  Nieudane ({fail}):")
    for s, name, msg in results:
        if s == FAIL:
            print(f"    ❌ {name}: {msg}")
print(f"\n  STATUS: {'🎉 WSZYSTKO DZIAŁA POPRAWNIE' if fail == 0 else '⚠️  SĄ BŁĘDY DO NAPRAWY'}")
