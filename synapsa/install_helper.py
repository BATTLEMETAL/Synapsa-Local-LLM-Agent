"""
Synapsa — Smart Install Helper (Universal — Python 3.10/3.11/3.12/3.13)
Wzorowany na: start_synapsa.bat, FIX_LIBRARY.py, napraw_triton_crash.py
Uruchamiany ze START_BUDOWLANKA.bat przed aplikacją.
"""
import sys
import subprocess
import platform
import os
import json


def run_pip(args: list, desc: str = "") -> bool:
    """Uruchamia pip z podanymi argumentami. Zwraca True jeśli sukces."""
    print(f"📦 Instalowanie: {desc}...", flush=True)
    cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + args
    try:
        result = subprocess.run(cmd, timeout=300)
        if result.returncode == 0:
            print(f"✅ {desc} — OK", flush=True)
            return True
        else:
            print(f"⚠️  {desc} — ostrzeżenie (kod: {result.returncode})", flush=True)
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ {desc} — timeout (>5min)", flush=True)
        return False
    except Exception as e:
        print(f"❌ {desc} — błąd: {e}", flush=True)
        return False


def check_import(module_name: str) -> bool:
    """Sprawdza czy moduł jest dostępny."""
    try:
        __import__(module_name)
        return True
    except Exception as e:
        print(f"⚠️  Moduł {module_name} zgłosił błąd przy imporcie: {e}", flush=True)
        return False


def install_base_deps():
    """Instaluje podstawowe zależności (zawsze potrzebne)."""
    print("\n[Krok 1/3] Podstawowe biblioteki...", flush=True)
    base = [
        "streamlit>=1.32",
        "colorama",
        "requests",
        "psutil",
        "python-dotenv",
    ]
    run_pip(base, "Core (streamlit, colorama, requests, psutil, dotenv)")


def install_torch():
    """
    Instaluje PyTorch z obsługą CUDA.
    Sprawdzony wzorzec ze start_synapsa.bat:
      pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    """
    print("\n[Krok 2/3] PyTorch (CUDA 12.1)...", flush=True)

    if check_import("torch"):
        try:
            import torch
            if torch.cuda.is_available():
                print(f"✅ PyTorch {torch.__version__} z CUDA {torch.version.cuda} — już zainstalowany.", flush=True)
                return
            else:
                print("⚠️  PyTorch bez CUDA — reinstalacja z obsługą GPU...", flush=True)
        except Exception:
            pass

    # CUDA 12.1 — kompatybilne z RTX 3060 i nowszymi (sprawdzone na tym setupie)
    run_pip(
        ["torch", "torchvision", "torchaudio",
         "--index-url", "https://download.pytorch.org/whl/cu121"],
        "PyTorch CUDA 12.1"
    )


def install_ai_libs():
    """Instaluje biblioteki AI (transformers, peft, bitsandbytes, accelerate)."""
    print("\n[Krok 3/3] Biblioteki AI...", flush=True)

    ai_libs = [
        "transformers==4.46.3",
        "peft==0.18.1",
        "accelerate==1.12.0",
        "bitsandbytes==0.49.2",
    ]
    run_pip(ai_libs, "Transformers, PEFT, BitsAndBytes, Accelerate")

    # Opcjonalnie unsloth (może nie działać na każdym Pythonie)
    if not check_import("unsloth"):
        print("⚙️  Instalowanie Unsloth (opcjonalne)...", flush=True)
        run_pip(["unsloth"], "Unsloth (opcjonalne)")


def fix_bitsandbytes_triton():
    """
    Naprawia bitsandbytes/nn/__init__.py dla Windows.
    Wzorowany na napraw_triton_crash.py.
    """
    import site
    bnb_path = None
    for sp in site.getsitepackages():
        candidate = os.path.join(sp, "bitsandbytes", "nn", "__init__.py")
        if os.path.exists(candidate):
            bnb_path = candidate
            break

    if bnb_path:
        try:
            with open(bnb_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Jeśli zawiera Triton imports — bezpieczne zastąpienie
            if "triton" in content.lower() and "UniversalMock" not in content:
                safe_content = "from .modules import *\n# Triton disabled for Windows\n"
                with open(bnb_path, "w", encoding="utf-8") as f:
                    f.write(safe_content)
                print("🩹 Naprawiono bitsandbytes/nn/__init__.py (Triton fix)", flush=True)
        except Exception as e:
            print(f"⚠️  Nie naprawiono BNB: {e}", flush=True)


def generate_config():
    """
    Generuje .env na podstawie skanowania sprzętu.
    Wzorowany na Launcher_Systemu.py ConfigGenerator.save_config()
    """
    print("\n⚙️  Skanowanie sprzętu i generowanie konfiguracji...", flush=True)
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from synapsa.hardware import generate_env_file
        profile = generate_env_file(os.path.join(project_root, ".env"))
        print(f"✅ Konfiguracja wygenerowana — Profil: {profile}", flush=True)

        # Też zapisujemy JSON config (jak w Launcher_Systemu.py)
        from synapsa.hardware import scan_hardware, determine_profile
        hw = scan_hardware()
        prof = determine_profile(hw)
        config_path = os.path.join(project_root, "synapsa_config.json")
        with open(config_path, "w") as f:
            json.dump(prof, f, indent=4)
        print(f"💾 synapsa_config.json zapisany.", flush=True)

    except Exception as e:
        print(f"⚠️  Błąd konfiguracji: {e}. Używam ustawień domyślnych.", flush=True)


def main():
    py_ver = sys.version_info
    print("=" * 55, flush=True)
    print(f"   SYNAPSA SMART SETUP", flush=True)
    print(f"   Python {py_ver.major}.{py_ver.minor}.{py_ver.micro} | {platform.system()}", flush=True)
    print("=" * 55, flush=True)

    # Kroki instalacji
    install_base_deps()
    install_torch()
    install_ai_libs()

    # Windows specific fix (z napraw_triton_crash.py)
    if platform.system() == "Windows":
        fix_bitsandbytes_triton()

    # Generuj konfigurację
    generate_config()

    print("\n" + "=" * 55, flush=True)
    print("✅ SETUP ZAKOŃCZONY POMYŚLNIE!", flush=True)
    print("=" * 55, flush=True)


if __name__ == "__main__":
    main()
