"""
Synapsa — Hardware Scanner & Auto-Config
Wzorowany na: Launcher_Systemu.py (HardwareScanner + ConfigGenerator)
"""
import os
import json
import platform
import psutil
import sys


def scan_hardware() -> dict:
    """Skanuje sprzęt i zwraca pełny raport. (Based on Launcher_Systemu.py)"""
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu": {
            "name": platform.processor() or "Unknown",
            "cores_physical": psutil.cpu_count(logical=False) or 1,
            "cores_logical": psutil.cpu_count(logical=True) or 1,
            "frequency_mhz": round(psutil.cpu_freq().current) if psutil.cpu_freq() else 0,
        },
        "ram": {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 1),
            "used_pct": psutil.virtual_memory().percent,
        },
        "disk": {"total_gb": 0, "free_gb": 0},
        "gpu": {"available": False},
    }

    # Disk
    try:
        disk_path = "C:\\" if platform.system() == "Windows" else "/"
        disk = psutil.disk_usage(disk_path)
        info["disk"]["total_gb"] = round(disk.total / (1024**3), 1)
        info["disk"]["free_gb"] = round(disk.free / (1024**3), 1)
    except Exception:
        pass

    # GPU (Wzorowane na Launcher_Systemu.py HardwareScanner.scan())
    try:
        import torch
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            mem_total = props.total_memory
            mem_used = torch.cuda.memory_allocated(0)
            info["gpu"] = {
                "available": True,
                "name": torch.cuda.get_device_name(0),
                "vram_total_gb": round(mem_total / (1024**3), 1),
                "vram_used_gb": round(mem_used / (1024**3), 1),
                "vram_free_gb": round((mem_total - mem_used) / (1024**3), 1),
                "cuda_version": torch.version.cuda or "N/A",
                "compute_capability": f"{props.major}.{props.minor}",
            }
    except Exception:
        pass

    # WMI / OS Fallback for GPU detection if torch is not available or CPU-only
    if not info["gpu"].get("available") and platform.system() == "Windows":
        try:
            import subprocess
            cmd = 'powershell -NoProfile -Command "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"'
            output = subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
            if output:
                # We might have multiple GPUs (e.g. integrated + dedicated), take the first or the non-Intel one
                gpu_lines = [line.strip() for line in output.split('\\n') if line.strip()]
                if gpu_lines:
                    gpu_name = gpu_lines[0]
                    for name in gpu_lines:
                        if "NVIDIA" in name or "Radeon" in name:
                            gpu_name = name
                            break
                    info["gpu"] = {
                        "available": False,  # False because AI engine cannot use it without CUDA
                        "name": f"{gpu_name} (Brak CUDA PyTorch)",
                        "vram_total_gb": 0,
                        "vram_used_gb": 0,
                        "vram_free_gb": 0,
                        "cuda_version": "N/A",
                        "compute_capability": "N/A",
                    }
        except Exception:
            pass

    return info


def determine_profile(hw: dict) -> dict:
    """
    Dobiera optymalny profil na podstawie sprzętu.
    Logika wzorowana na Launcher_Systemu.py ConfigGenerator.determine_profile()
    z rozszerzeniem o parametry MAX_SEQ_LENGTH i device.
    """
    gpu = hw.get("gpu", {})
    ram = hw.get("ram", {})
    ram_gb = ram.get("total_gb", 0)

    if gpu.get("available"):
        vram = gpu.get("vram_total_gb", 0)

        # POZIOM 1: Bestia (RTX 3090/4090, 20GB+)
        if vram >= 20 and ram_gb >= 32:
            return {
                "profile": "GOD_MODE",
                "description": "Full power: 7B+ model, 4-bit, max context",
                "tier": "GOD_MODE",
                "device": "cuda",
                "max_seq_length": 8192,
                "batch_size": 4,
                "model_size": "7b",
                "quantization": "4bit",
                "context_window": 8192,
                "gpu_layers": -1,
                "cpu_offload": False,
            }
        # POZIOM 2: RTX 3060 12GB (Twój Komputer)
        elif vram >= 10:
            return {
                "profile": "HIGH_PERFORMANCE",
                "description": "GPU-optimized: 7B 4-bit, balanced context (RTX 3060/3070)",
                "tier": "HIGH_PERFORMANCE",
                "device": "cuda",
                "max_seq_length": 4096,
                "batch_size": 2,
                "model_size": "7b",
                "quantization": "4bit",
                "context_window": 4096,
                "gpu_layers": -1,
                "cpu_offload": True,  # Safety for 12GB
            }
        # POZIOM 3: Słabsze GPU (RTX 3050/1060 - 6GB)
        elif vram >= 6:
            return {
                "profile": "MID_PERFORMANCE",
                "description": "Mid GPU: 7B 4-bit, reduced context",
                "tier": "MID_PERFORMANCE",
                "device": "cuda",
                "max_seq_length": 2048,
                "batch_size": 1,
                "model_size": "7b",
                "quantization": "4bit",
                "context_window": 2048,
                "gpu_layers": -1,
                "cpu_offload": True,
            }
        # POZIOM 4: Słabe GPU (<6GB) - CPU offload
        else:
            return {
                "profile": "CPU_FALLBACK",
                "description": "GPU detected but VRAM < 6GB — CPU offload mode",
                "tier": "CPU_FALLBACK",
                "device": "cuda",
                "max_seq_length": 512,
                "batch_size": 1,
                "model_size": "1.5b",
                "quantization": "4bit",
                "context_window": 1024,
                "gpu_layers": 20,
                "cpu_offload": True,
            }
    else:
        # CPU only
        if ram_gb >= 32:
            return {
                "profile": "CPU_WORKHORSE",
                "description": "CPU-only with high RAM (32GB+) — llama.cpp recommended",
                "tier": "CPU_WORKHORSE",
                "device": "cpu",
                "max_seq_length": 2048,
                "batch_size": 1,
                "model_size": "7b",
                "quantization": "4bit",
                "context_window": 2048,
                "gpu_layers": 0,
                "cpu_offload": False,
            }
        elif ram_gb >= 16:
            return {
                "profile": "CPU_STANDARD",
                "description": "CPU-only standard (16GB RAM)",
                "tier": "CPU_STANDARD",
                "device": "cpu",
                "max_seq_length": 1024,
                "batch_size": 1,
                "model_size": "1.5b",
                "quantization": "4bit",
                "context_window": 1024,
                "gpu_layers": 0,
                "cpu_offload": False,
            }
        elif ram_gb >= 8:
            return {
                "profile": "POTATO_MODE",
                "description": "Low RAM CPU-only mode (8GB) — odpowiedzi mogą być wolne",
                "tier": "POTATO_MODE",
                "device": "cpu",
                "max_seq_length": 512,
                "batch_size": 1,
                "model_size": "1.5b",
                "quantization": "4bit",
                "context_window": 512,
                "gpu_layers": 0,
                "cpu_offload": False,
            }
        else:
            return {
                "profile": "INCOMPATIBLE",
                "description": "Ten komputer to toster — min. 8GB RAM wymagane.",
                "tier": "INCOMPATIBLE",
                "device": "cpu",
                "max_seq_length": 256,
                "batch_size": 1,
                "context_window": 256,
                "gpu_layers": 0,
                "cpu_offload": False,
            }


def generate_env_file(output_path: str = ".env") -> str:
    """Skanuje sprzęt i generuje plik .env dopasowany do profilu."""
    hw = scan_hardware()
    profile = determine_profile(hw)

    content = f"""# Synapsa Configuration (Auto-Generated)
# Profile: {profile['profile']} | Desc: {profile['description']}
# Python: {platform.python_version()} | OS: {platform.system()}

# --- API KEYS (Optional — wypełnij dla trybu chmury) ---
GEMINI_API_KEY=
GROQ_API_KEY=

# --- MODEL ---
MODEL_PATH=unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit
ADAPTER_PATH=moje_ai_adaptery

# --- HARDWARE (Auto-detected) ---
DEVICE={profile['device']}
MAX_SEQ_LENGTH={profile['max_seq_length']}
BNB_CPU_OFFLOAD={'1' if profile.get('cpu_offload') else '0'}

# --- PATHS ---
PROJECT_SCAN_PATH=
ANDROID_SCAN_PATH=

# --- WINDOWS COMPAT ---
XFORMERS_FORCE_DISABLE_TRITON=1
WBITS_USE_TRITON=0
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return profile['profile']
