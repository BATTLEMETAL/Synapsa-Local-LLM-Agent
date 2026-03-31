import os
import sys
import subprocess
import platform

def find_nvidia_gpu():
    print("🔍 Skanowanie w poszukiwaniu kart graficznych NVIDIA...", flush=True)
    if platform.system() == "Windows":
        try:
            cmd = 'powershell -NoProfile -Command "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"'
            output = subprocess.check_output(cmd, shell=True, text=True).strip()
            for line in output.split('\n'):
                if "NVIDIA" in line.upper():
                    return line.strip()
        except:
            pass
    return None

def main():
    print("=" * 60)
    print("   SYNAPSA — AUTOMATYCZNA NAPRAWA AKCELERACJI GPU (CUDA)")
    print("=" * 60)

    gpu_name = find_nvidia_gpu()
    if not gpu_name:
        print("⚠️  Nie wykryto karty graficznej NVIDIA zgodnej z CUDA w tym systemie.")
        print("Aplikacja pozostanie w stabilnym trybie awaryjnym CPU (POTATO_MODE).")
        input("Naciśnij Enter, aby zakończyć...")
        sys.exit(0)

    print(f"✅ Znaleziono zgodny sprzęt: {gpu_name}")
    print("Sprawdzam aktualną wersję silnika AI (PyTorch)...")

    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ Akceleracja sprzętowa jest już poprawnie zainstalowana i aktywna!")
            print(f"Wersja CUDA: {torch.version.cuda}")
            print(f"Wykryto urządzeń: {torch.cuda.device_count()}")
            input("Naciśnij Enter, aby zakończyć...")
            sys.exit(0)
        else:
            print("⚠️ PyTorch jest zainstalowany w wersji procesorowej (CPU-only).")
    except ImportError:
        print("⚠️ PyTorch nie jest zainstalowany.")

    print("\n" + "=" * 60)
    print("🛠️  ROZPOCZYNAM NAPRAWĘ: Instalowanie sterowników silnika CUDA...")
    print("To może potrwać kilka minut - pobierane jest ok. 2-3 GB danych.")
    print("Proszę NIE zamykać tego okna.")
    print("=" * 60)

    # Najpierw usuwamy starą wersję, żeby uniknąć konfliktów
    print("\n[Krok 1/2] Usuwanie wersji procesorowej (CPU)...", flush=True)
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "torch", "torchvision", "torchaudio"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Instalujemy specjalnie zindeksowaną wersję cu121 (dla architektury Ampere/Ada, np. RTX 3060)
    print("[Krok 2/2] Pobieranie i instalacja modułu CUDA 12.1...", flush=True)
    cmd = [
        sys.executable, "-m", "pip", "install", 
        "torch", "torchvision", "torchaudio", 
        "--index-url", "https://download.pytorch.org/whl/cu121",
        "--upgrade", "--force-reinstall"
    ]
    
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("🎉 SUKCES! Akceleracja GPU pod kątem AI została pomyślnie wgrana.")
        print("Uruchom powownie 'START_BUDOWLANKA.bat'. System sam przydzieli profil HIGH_PERFORMANCE.")
        print("=" * 60)
    else:
        print("\n❌ Wystąpił błąd podczas pobierania paczek. Sprawdź połączenie z internetem.")
    
    input("Naciśnij Enter, aby zakończyć...")

if __name__ == "__main__":
    main()
