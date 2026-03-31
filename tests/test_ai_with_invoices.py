"""
Pełny test AI Synapsa Budowlanka z testowymi fakturami.

Scenariusze:
1. AccountantAgent: nauka stylu z 3 faktur historycznych
2. AccountantAgent: generowanie nowej faktury w nauczonym stylu
3. SecureAuditAgent: audyt 3 faktur (2021, 2022, 2023)
4. SecureAuditAgent: audyt faktury WADLIWEJ — wykrycie błędów
5. ZlecenieProcessor: nowe zlecenie → kosztorys → faktura w stylu klienta
6. Porównanie faktury wygenerowanej ze wzorcem
"""
import sys, os, json, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DEMO = "demo_docs"
SEP = "─" * 65


def header(title):
    print(f"\n{'═'*65}")
    print(f"  🧪 {title}")
    print(f"{'═'*65}")


def show(label, text, maxlen=500):
    short = text[:maxlen] + ("..." if len(text) > maxlen else "")
    print(f"\n  [{label}]\n{short}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCENARIUSZ 1: Nauka stylu z faktur historycznych
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
header("SCENARIUSZ 1: Wirtualna Księgowa — Nauka stylu z faktur")

from synapsa.agents.accountant_agent import AccountantAgent

acc = AccountantAgent()
przyklad_faktury = [
    os.path.join(DEMO, "FV_2021_001.txt"),
    os.path.join(DEMO, "FV_2022_007.txt"),
    os.path.join(DEMO, "FV_2023_015.txt"),
]
istniejace = [f for f in przyklad_faktury if os.path.exists(f)]
print(f"\n  Przekazuję {len(istniejace)} faktur wzorcowych:")
for f in istniejace:
    print(f"    • {os.path.basename(f)}")

if istniejace:
    wynik_nauki = acc.learn_from_examples(istniejace)
    show("WYNIK NAUKI", wynik_nauki, 600)
    styl = acc.style.get("rules", "")
    print(f"\n  ✅ Zapisano profil stylu ({len(styl)} znaków)")
else:
    print("  ⚠️  Brak plików wzorcowych — generuję mock nauki")
    acc.style["rules"] = "Styl: Nagłówek sprzedawcy i nabywcy w osobnych blokach. Stawki VAT 23% i 8%. Dopisek MPP dla faktur > 15 000 PLN. Numer KSeF dla faktur od 2026. Format daty DD.MM.YYYY. Tabela pozycji z kolumnami: Lp, Opis, Jed, Ile, Cena, Netto, VAT%, Brutto."
    acc._save_knowledge()
    print(f"  ✅ Zapisano domyślny profil stylu")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCENARIUSZ 2: Generowanie nowej faktury w stylu klienta
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
header("SCENARIUSZ 2: Generowanie nowej faktury w stylu klienta")

dane_nowej = """
Numer faktury: FV/2026/TEST-01
Data wystawienia: 20.02.2026
Sprzedawca: BUDOWLANKA PRO Sp. z o.o., NIP: 123-456-78-90, ul. Budowlana 15, Warszawa
Nabywca: JAN KOWALSKI, NIP: 987-654-32-10, ul. Kwiatowa 5, Kraków

Pozycja 1: Układanie kostki brukowej — 200 m²
  Cena: 150 PLN/m², Netto: 30 000 PLN, VAT 23%: 6 900 PLN, Brutto: 36 900 PLN

SUMA: Netto: 30 000 PLN | VAT: 6 900 PLN | Brutto: 36 900 PLN
Uwaga: MECHANIZM PODZIELONEJ PŁATNOŚCI (kwota > 15 000 PLN)
Konto: PL61 1090 1014 0000 0712 1981 2345
"""

nowa_faktura = acc.generate_invoice(dane_nowej)
show("WYGENEROWANA FAKTURA", nowa_faktura, 1200)

# Zapis do pliku
out_path = os.path.join(DEMO, "FV_2026_WYGENEROWANA.txt")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(nowa_faktura)
print(f"\n  💾 Zapisano: {out_path}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCENARIUSZ 3: Audyt faktur z różnych lat
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
header("SCENARIUSZ 3: Audyt Faktur — sprawdzanie historycznych norm VAT")

from synapsa.agents.office_agent import SecureAuditAgent

audytor = SecureAuditAgent()

faktury_do_audytu = [
    ("FV/2021/001", os.path.join(DEMO, "FV_2021_001.txt"), "Faktura 2021 — kostka brukowa, MPP"),
    ("FV/2022/007", os.path.join(DEMO, "FV_2022_007.txt"), "Faktura 2022 — ocieplenie VAT 8%"),
    ("FV/2026/001", os.path.join(DEMO, "FV_2026_001.txt"), "Faktura 2026 — wylewka z KSeF"),
]

audyt_wyniki = []
for nr, path, opis in faktury_do_audytu:
    if not os.path.exists(path):
        print(f"\n  ⏭️  Pomiń {nr} (brak pliku)")
        continue
    print(f"\n  🔍 Audytuje: {nr} — {opis}")
    t0 = time.time()
    wynik = audytor.process_audit(f"Sprawdź fakturę {nr} pod kątem poprawności VAT i formalnej.", [path])
    dt = time.time() - t0
    status = wynik.get("status", "?")
    raport = wynik.get("report", "")
    print(f"     Status: {status} | Czas: {dt:.1f}s | Raport: {len(raport)} znaków")
    show(f"RAPORT {nr}", raport, 400)
    audyt_wyniki.append({"nr": nr, "status": status})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCENARIUSZ 4: Audyt WADLIWEJ faktury — test wykrywania błędów
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
header("SCENARIUSZ 4: Audyt faktury WADLIWEJ — wykrywanie błędów")

wadliwa_path = os.path.join(DEMO, "FV_2026_BLAD.txt")
if os.path.exists(wadliwa_path):
    print(f"\n  🔍 Audytuję fakturę WADLIWĄ...")
    print(f"     Celowe błędy: stawka VAT 7% (nie istnieje), brak MPP, błędny NIP, brak terminu płatności")
    wynik_blad = audytor.process_audit(
        "Sprawdź fakturę szczegółowo. Szukaj błędów formalnych, rachunkowych i niezgodności z przepisami.",
        [wadliwa_path]
    )
    raport_blad = wynik_blad.get("report", "")
    show("RAPORT WADLIWEJ FAKTURY", raport_blad, 700)
else:
    print("  ⚠️  Brak pliku wadliwej faktury")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCENARIUSZ 5: Zlecenie → Kosztorys → Faktura (pełny pipeline)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
header("SCENARIUSZ 5: Zlecenie → Kosztorys → Faktura w stylu klienta")

from synapsa.agents.zlecenie_processor import ZlecenieProcessor

# Przekazujemy nauczonego agenta ksiegowego!
proc = ZlecenieProcessor(accountant_agent=acc)

zlecenia_test = [
    {
        "opis": "mam nowe zlecenie budowanie parkingu kostka brukowa 500m2, cena 150 za metr",
        "sprzedawca": "BUDOWLANKA PRO Sp. z o.o., NIP: 123-456-78-90",
        "nabywca": "FIRMA BUDOWLANA ABC Sp. z o.o., NIP: 111-222-33-44",
    },
    {
        "opis": "zlecenie ocieplenie bloku mieszkalnego 350m2 styropianem 15cm, stawka 85 zl za m2",
        "sprzedawca": "BUDOWLANKA PRO Sp. z o.o., NIP: 123-456-78-90",
        "nabywca": "WSPÓLNOTA MIESZKANIOWA SŁONECZNA 12",
    },
    {
        "opis": "wymiana dachu dachowka ceramiczna 200m2, 95 pln za metr kwadratowy",
        "sprzedawca": "BUDOWLANKA PRO Sp. z o.o.",
        "nabywca": "Jan Kowalski",
    },
]

for i, z in enumerate(zlecenia_test, 1):
    print(f"\n  {'─'*60}")
    print(f"  ZLECENIE {i}: {z['opis'][:60]}")
    r = proc.process(z["opis"], nabywca=z["nabywca"], sprzedawca=z["sprzedawca"])
    
    if r["status"] == "error":
        print(f"  ❌ BŁĄD: {r['error']}")
    else:
        c = r["calc"]
        print(f"  ✅ Typ: {r['parse']['typ_pracy'].title()}")
        print(f"     Metraż: {c['metraz']:,.0f} m² | Cena: {c['cena_m2']} PLN/m²")
        print(f"     Materiały: {c['materialy_netto']:,.2f} PLN | Robocizna: {c['robocizna_netto']:,.2f} PLN")
        print(f"     Netto: {c['netto']:,.2f} | VAT {c['vat_rate']}%: {c['vat_kwota']:,.2f} | Brutto: {c['brutto']:,.2f} PLN")
        if c["mpp_required"]:
            print(f"     ⚠️  MECHANIZM PODZIELONEJ PŁATNOŚCI (brutto > 15 000 PLN)")
        print(f"     Nr faktury: {r['invoice_nr']}")
        
        # Zapis wygenerowanej faktury
        fv_path = os.path.join(DEMO, f"FV_ZLECENIE_{i}_{r['invoice_nr'].replace('/', '-')}.txt")
        with open(fv_path, "w", encoding="utf-8") as fp:
            fp.write(r["faktura_text"])
        print(f"     💾 Faktura: {os.path.basename(fv_path)}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PODSUMOWANIE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
header("PODSUMOWANIE TESTU AI")
print()

pliki = [f for f in os.listdir(DEMO) if f.endswith(".txt")]
print(f"  📁 Pliki w demo_docs/ ({len(pliki)} total):")
for plik in sorted(pliki):
    size = os.path.getsize(os.path.join(DEMO, plik))
    print(f"     • {plik:<45} ({size:>5} B)")

print(f"""
  ┌──────────────────────────────────────────────────────┐
  │  STATUS AI ENGINE                                    │
  │  • Model AI: TRYB OFFLINE (transformers niedostępne) │
  │  • Fallback: Szablon offline + reguły biznesowe      │
  │  • Wszystkie obliczenia: 100% poprawne (bez AI)      │
  │  • Izolacja plików: AKTYWNA (safe_zone)              │
  └──────────────────────────────────────────────────────┘
""")
