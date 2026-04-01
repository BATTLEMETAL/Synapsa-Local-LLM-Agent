import os
import sys
import site


def force_fix_bnb_init():
    print("🩹 OSTATECZNA NAPRAWA bitsandbytes/nn/__init__.py ...")

    # 1. Szukanie biblioteki
    bnb_path = None
    for sp in site.getsitepackages():
        check_path = os.path.join(sp, "bitsandbytes")
        if os.path.exists(check_path):
            bnb_path = check_path
            break

    if not bnb_path:
        bnb_path = os.path.join(sys.prefix, "Lib", "site-packages", "bitsandbytes")

    if not bnb_path or not os.path.exists(bnb_path):
        print("❌ Nie znaleziono folderu bitsandbytes.")
        return

    # 2. Ścieżka do pliku
    target_file = os.path.join(bnb_path, "nn", "__init__.py")

    print(f"📄 Nadpisuję plik: {target_file}")

    # 3. BEZPIECZNA ZAWARTOŚĆ
    # Zamiast skomplikowanych importów Tritona, zostawiamy tylko podstawy.
    safe_content = """
from .modules import *
# Triton modules disabled for Windows compatibility
"""

    try:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(safe_content)
        print("✅ SUKCES! Plik został nadpisany bezpieczną wersją. Błąd nawiasu zniknie.")
    except Exception as e:
        print(f"❌ Błąd zapisu: {e}")


if __name__ == "__main__":
    force_fix_bnb_init()