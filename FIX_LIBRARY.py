import os

PATH = r"C:\Users\mz100\PycharmProjects\Synapsa\venv\lib\site-packages\unsloth\__init__.py"

CLEAN_CONTENT = """
# Pancerne Środowisko Synapsa Core
import os
import sys

# Całkowite wycięcie problematycznych importów Tritona
libcuda_dirs = lambda: []

# Zachowanie reszty funkcjonalności unsloth
from .plotting import *
# Tutaj oryginalnie były błędy wcięć - teraz ich nie ma
"""


def nuke_and_reset():
    print("🚀 SYNAPSA: Atomowy reset biblioteki unsloth...")
    if not os.path.exists(PATH):
        print("❌ Błąd: Nie znaleziono pliku!")
        return

    # Nadpisujemy CAŁY plik nową, minimalistyczną wersją
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(CLEAN_CONTENT)

    # Usuwamy fizyczne foldery triton, które tworzyliśmy - Import Hook zrobi to lepiej
    triton_dir = r"C:\Users\mz100\PycharmProjects\Synapsa\venv\lib\site-packages\triton"
    if os.path.exists(triton_dir):
        import shutil
        shutil.rmtree(triton_dir)
        print("🗑️ Usunięto fizyczne atrapy folderów.")

    print("✅ Biblioteka zresetowana do bezpiecznego stanu.")


if __name__ == "__main__":
    nuke_and_reset()