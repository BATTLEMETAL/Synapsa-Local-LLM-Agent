import os
import json

DATASET_FILE = "moj_finalny_dataset.jsonl"
BACKUP_FILE = "moj_finalny_dataset.jsonl.bak_full"

# Lista sygnatur, które oznaczają "zły/stary kod", którego chcemy się pozbyć
BAD_SIGNATURES = [
    "admin_super_secret_key_123",  # Z pliku niebezpieczne_api.py
    "BloatedActivity",  # Z pliku BloatedActivity.java
    "mysqli_connect",  # Z pliku legacy_produkt.php
    "<script>alert('hacked')</script>",  # Z pliku legacy_produkt.php
    "admin' --",  # Z komentarza o SQL Injection
    "God Class",  # Z komentarza w Java
]


def clean_dataset():
    if not os.path.exists(DATASET_FILE):
        print(f"❌ Nie znaleziono pliku {DATASET_FILE}")
        return

    print(f"🧹 Rozpoczynam KOMPLEKSOWE czyszczenie bazy '{DATASET_FILE}'...")

    # Kopia zapasowa
    if os.path.exists(BACKUP_FILE):
        os.remove(BACKUP_FILE)
    os.rename(DATASET_FILE, BACKUP_FILE)
    print(f"📦 Kopia zapasowa: {BACKUP_FILE}")

    stats = {
        "kept": 0,
        "removed_content": 0,
        "fixed_types": 0,
        "removed_error": 0
    }

    with open(BACKUP_FILE, 'r', encoding='utf-8') as infile, \
            open(DATASET_FILE, 'w', encoding='utf-8') as outfile:

        for line_num, line in enumerate(infile):
            line = line.strip()
            if not line: continue

            # 1. FILTR TREŚCI (Szybki skan tekstu)
            # Jeśli linia zawiera złe słowa, od razu ją wyrzucamy
            if any(sig in line for sig in BAD_SIGNATURES):
                stats["removed_content"] += 1
                continue

            try:
                data = json.loads(line)

                # 2. NAPRAWA TYPÓW (To naprawia błąd Trenera!)
                # Upewniamy się, że 'input', 'instruction' i 'output' to ZAWSZE stringi
                was_fixed = False

                for field in ['instruction', 'input', 'output']:
                    val = data.get(field)

                    if val is None:
                        data[field] = ""
                        was_fixed = True
                    elif not isinstance(val, str):
                        # Jeśli to słownik/lista/liczba -> zamień na napis
                        data[field] = json.dumps(val, ensure_ascii=False)
                        was_fixed = True

                if was_fixed:
                    stats["fixed_types"] += 1

                # Zapisujemy czystą linię
                outfile.write(json.dumps(data, ensure_ascii=False) + "\n")
                stats["kept"] += 1

            except json.JSONDecodeError:
                # Jeśli linia jest po prostu uszkodzona składniowo
                stats["removed_error"] += 1
                print(f"⚠️ Usunięto uszkodzony JSON w linii {line_num + 1}")

    print("-" * 40)
    print(f"✅ SKOŃCZONE.")
    print(f"   Zachowano (dobre):         {stats['kept']}")
    print(f"   Usunięto (złe sygnatury):  {stats['removed_content']}")
    print(f"   Naprawiono (błędy typów):  {stats['fixed_types']}  <-- To naprawi crash Trenera")
    print(f"   Usunięto (błędy JSON):     {stats['removed_error']}")
    print("-" * 40)
    print("👉 Teraz możesz bezpiecznie odpalić: python trener.py")


if __name__ == "__main__":
    clean_dataset()