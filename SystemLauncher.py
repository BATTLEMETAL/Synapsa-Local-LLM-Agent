import os
import sys
import psutil
import json
import torch
import warnings

# Wyłączamy zbędne logi
warnings.filterwarnings("ignore")


class HardwareScanner:
    def __init__(self):
        self.specs = {
            "ram_total_gb": 0,
            "has_nvidia": False,
            "vram_gb": 0,
            "cpu_threads": 0,
            "platform": sys.platform
        }

    def scan(self):
        print("🕵️  Skanowanie sprzętu...")

        # 1. RAM
        vm = psutil.virtual_memory()
        self.specs["ram_total_gb"] = round(vm.total / (1024 ** 3), 1)

        # 2. CPU
        self.specs["cpu_threads"] = psutil.cpu_count(logical=True)

        # 3. GPU (Nvidia)
        try:
            if torch.cuda.is_available():
                self.specs["has_nvidia"] = True
                # Pobieramy ilość VRAM z pierwszej karty
                props = torch.cuda.get_device_properties(0)
                self.specs["vram_gb"] = round(props.total_memory / (1024 ** 3), 1)
                self.specs["gpu_name"] = torch.cuda.get_device_name(0)
            else:
                self.specs["has_nvidia"] = False
        except:
            self.specs["has_nvidia"] = False

        print(f"   ✅ Wykryto: RAM: {self.specs['ram_total_gb']}GB | CPU: {self.specs['cpu_threads']} wątków")
        if self.specs["has_nvidia"]:
            print(f"   ✅ GPU: {self.specs['gpu_name']} ({self.specs['vram_gb']} GB VRAM)")
        else:
            print("   ⚠️  Brak dedykowanej karty NVIDIA (Tryb CPU/GGUF).")

        return self.specs


class ConfigGenerator:
    def __init__(self, specs):
        self.specs = specs

    def determine_profile(self):
        # LOGIKA BIZNESOWA DOBIERANIA WERSJI

        # --- POZIOM 1: Bestia (RTX 3090/4090) ---
        if self.specs["has_nvidia"] and self.specs["vram_gb"] >= 20:
            return {
                "tier": "GOD_MODE",
                "engine": "unsloth_cuda",
                "model_size": "7b",
                "quantization": "4bit",  # Można by 8bit, ale 4bit jest szybsze
                "context_window": 8192,
                "gpu_layers": -1  # Wszystko na GPU
            }

        # --- POZIOM 2: Twój Komputer (RTX 3060 - 12GB) ---
        elif self.specs["has_nvidia"] and self.specs["vram_gb"] >= 10:
            return {
                "tier": "HIGH_PERFORMANCE",
                "engine": "unsloth_cuda",
                "model_size": "7b",
                "quantization": "4bit",
                "context_window": 4096,
                "gpu_layers": -1
            }

        # --- POZIOM 3: Słabsze GPU (RTX 3050 / 1060 - 6GB) ---
        elif self.specs["has_nvidia"] and self.specs["vram_gb"] >= 6:
            return {
                "tier": "MID_PERFORMANCE",
                "engine": "unsloth_cuda",  # Nadal CUDA, ale ostrożnie
                "model_size": "7b",
                "quantization": "4bit",
                "context_window": 2048,  # Tniemy kontekst
                "gpu_layers": -1
            }

        # --- POZIOM 4: Laptop Biurowy (Brak GPU lub <4GB VRAM) ---
        # Tutaj musimy zmienić silnik na GGUF (Llama.cpp), bo Unsloth nie ruszy
        else:
            # Sprawdzamy czy ma chociaż RAM
            if self.specs["ram_total_gb"] >= 16:
                return {
                    "tier": "CPU_WORKHORSE",
                    "engine": "llama_cpp",  # ZMIANA SILNIKA!
                    "model_file": "synapsa-7b-q4_k_m.gguf",
                    "context_window": 4096,
                    "threads": max(1, self.specs["cpu_threads"] - 2)
                }
            elif self.specs["ram_total_gb"] >= 8:
                return {
                    "tier": "POTATO_MODE",
                    "engine": "llama_cpp",
                    "model_file": "synapsa-7b-q2_k.gguf",  # Bardzo mocna kompresja (głupszy model)
                    "context_window": 2048,
                    "threads": max(1, self.specs["cpu_threads"] - 2)
                }
            else:
                return {
                    "tier": "INCOMPATIBLE",
                    "error": "Ten komputer to toster. Potrzebujesz min. 8GB RAM."
                }

    def save_config(self):
        profile = self.determine_profile()
        print(f"\n⚙️  Dobrano profil: \033[1m{profile['tier']}\033[0m")

        if profile.get("error"):
            print(f"❌ {profile['error']}")
            return False

        with open("synapsa_config.json", "w") as f:
            json.dump(profile, f, indent=4)
        print("💾 Zapisano ustawienia w 'synapsa_config.json'.")
        return True


if __name__ == "__main__":
    print("--- SYNAPSA LAUNCHER v1.0 ---")
    scanner = HardwareScanner()
    specs = scanner.scan()

    generator = ConfigGenerator(specs)
    generator.save_config()

    # Symulacja uruchomienia właściwej aplikacji
    if os.path.exists("synapsa_config.json"):
        with open("synapsa_config.json") as f:
            conf = json.load(f)

        print(f"\n🚀 Uruchamiam silnik: {conf.get('engine')}...")
        if conf.get('engine') == 'unsloth_cuda':
            print(f"   -> Ładowanie modelu Unsloth (Context: {conf['context_window']})")
            # import Start
        elif conf.get('engine') == 'llama_cpp':
            print(f"   -> Ładowanie Llama.cpp (CPU Threads: {conf['threads']})")
            # import StartGGUF