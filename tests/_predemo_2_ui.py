"""Test 2: Struktura kodu UI — weryfikacja app_budowlanka.py bez uruchamiania"""
import sys, os, ast

app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_budowlanka.py'))
with open(app_path, encoding='utf-8') as f:
    src = f.read()

# Sprawdz skladnie
try:
    ast.parse(src)
    print("[OK] app_budowlanka.py — brak bledow skladni Python")
except SyntaxError as e:
    print(f"[XX] BLAD SKLADNI: {e}")
    sys.exit(1)

checks = [
    ("Tab: 📋 Nowe Zlecenie",        "Nowe Zlecenie"),
    ("Tab: 💬 Asystent Budowlany",   "Asystent Budowlany"),
    ("Tab: 🕵️ Audyt Faktur",         "Audyt Faktur"),
    ("Tab: 👩 Wirtualna Ksiegowa",   "Wirtualna Ksi"),
    ("Tab: 🖥️ System & Sprzet",      "System"),
    ("Import ZlecenieProcessor",     "ZlecenieProcessor"),
    ("Pole tekstowe zlecenie_text",  "zlecenie_text"),
    ("Przycisk Oblicz i wystaw",     "Oblicz i wyst"),
    ("download_button faktury",      "download_button"),
    ("Pole nabywca (klient)",        "nabywca"),
    ("Pole sprzedawca (firma)",      "sprzedawca"),
    ("Przykladowe zlecenia (3 szt)", "Przyk"),
    ("Wyswietlanie kosztorysu",      "kosztorys"),
    ("Wyswietlanie faktury",         "faktura"),
    ("Historia zlecen w sesji",      "historia"),
]

all_ok = True
print("\n[STRUKTURA UI — app_budowlanka.py]")
for name, kw in checks:
    found = kw in src
    if not found:
        all_ok = False
    print(f"  [{'OK' if found else 'XX'}] {name}")

print()
print("WYNIK:", "STRUKTURA UI KOMPLETNA" if all_ok else "BRAKUJE ELEMENTOW UI!")
sys.exit(0 if all_ok else 1)
