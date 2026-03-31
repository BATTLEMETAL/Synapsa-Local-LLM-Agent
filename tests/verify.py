"""
Synapsa — System Verification Script
"""
import sys
import os
import time
import requests
import threading
import uvicorn
from contextlib import contextmanager

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_status(msg, status="OK"):
    color = "\033[92m" if status == "OK" else "\033[91m"
    end = "\033[0m"
    print(f"[{color}{status}{end}] {msg}")

def verify_imports():
    try:
        import synapsa.compat
        import synapsa.config
        import synapsa.utils
        import synapsa.engine
        import synapsa.memory
        import synapsa.hardware
        import synapsa.agents.auditor
        import synapsa.agents.coder
        import synapsa.agents.architect
        import synapsa.agents.scanner
        import synapsa.agents.observer
        import synapsa.agents.sensei
        import synapsa.agents.teacher
        import synapsa.training.trainer
        import synapsa.training.cleaner
        import synapsa.testing.validator
        import synapsa.api.app
        import synapsa.api.routes
        print_status("All modules imported successfully")
        return True
    except ImportError as e:
        print_status(f"Import failed: {e}", "FAIL")
        return False

def verify_config():
    from synapsa.config import settings
    # Check if critical env vars are potentially empty (just warning)
    if not settings.GEMINI_KEY:
        print_status("GEMINI_KEY is missing/empty", "WARN")
    else:
        print_status(f"GEMINI_KEY loaded ({len(settings.GEMINI_KEY)} chars)")
    
    if not settings.GROQ_KEY:
        print_status("GROQ_KEY is missing/empty", "WARN")
    
    print_status(f"Model Path: {settings.BASE_MODEL}")
    print_status(f"Dataset Path: {settings.DATASET_FILE}")
    return True

def verify_hardware():
    from synapsa.hardware import scan_hardware, determine_profile
    hw = scan_hardware()
    profile = determine_profile(hw)
    print_status(f"Hardware Scan: {hw['os']} / {hw['cpu']['name']}")
    
    gpu = hw.get('gpu', {})
    if gpu.get('available'):
        print_status(f"GPU Detected: {gpu['name']} ({gpu['vram_total_gb']} GB VRAM)")
    else:
        print_status("No GPU detected (running in CPU mode)", "WARN")
        
    print_status(f"Selected Profile: {profile['profile']}")
    return True

def verify_agents():
    # We will instantiate agents but NOT the engine to save time/memory in this quick check
    # But wait, agents init engine in constructor?
    # No, agents take engine in __init__ or lazy load in methods.
    # Let's check `auditor.py`: `def __init__(self, engine=None): ...`
    # Excellent, lazy loading.
    
    try:
        from synapsa.agents.auditor import HybridAuditor
        from synapsa.agents.coder import InteractiveCoder
        from synapsa.agents.architect import ProjectArchitect
        from synapsa.agents.scanner import DatasetScanner
        from synapsa.agents.observer import FileObserver
        from synapsa.agents.sensei import NightSensei
        from synapsa.agents.teacher import KnowledgeTeacher
        
        auditor = HybridAuditor(engine="mock")
        coder = InteractiveCoder(engine="mock")
        arch = ProjectArchitect(engine="mock")
        scanner = DatasetScanner(use_cloud_ai=False)
        observer = FileObserver()
        sensei = NightSensei(engine="mock")
        teacher = KnowledgeTeacher()
        
        print_status("All agents instantiated successfully")
        return True
    except Exception as e:
        print_status(f"Agent instantiation failed: {e}", "FAIL")
        return False

def start_server_thread():
    from synapsa.api.app import app
    print("DEBUG: Registered Routes:")
    for route in app.routes:
        print(f" - {route.path} ({route.name})")
        
    print("Starting API server in background thread...")
    config = uvicorn.Config(app, host="127.0.0.1", port=8001, log_level="info")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run)
    t.daemon = True
    t.start()
    time.sleep(5) # Wait for startup

def wait_for_api(timeout=120):
    """Czeka aż API wstanie."""
    start = time.time()
    url = "http://127.0.0.1:8001/api/v1/system/status"
    
    print(f"⏳ Waiting up to {timeout}s for API...")
    while time.time() - start < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print_status("API is up and running.")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.5)
    print_status("API did not start in time.", "FAIL")
    return False

def verify_api():
    try:
        start_server_thread()
        if not wait_for_api():
            return False

        response = requests.get("http://127.0.0.1:8001/api/v1/system/status")
        if response.status_code == 200:
            data = response.json()
            print_status(f"API Health Check Response: {data}")
            return True
        else:
            print_status(f"API returned status {response.status_code}", "FAIL")
            return False
    except Exception as e:
        print_status(f"API check failed: {e}", "FAIL")
        return False

if __name__ == "__main__":
    print("=== SYNAPSA SYSTEM VERIFICATION ===")
    
    steps = [
        verify_imports,
        verify_config,
        verify_hardware,
        verify_agents,
        verify_api
    ]
    
    success = True
    for step in steps:
        print("-" * 30)
        if not step():
            success = False
            
    print("-" * 30)
    if success:
        print("\033[92mALL SYSTEMS GO. READY FOR LAUNCH.\033[0m")
        sys.exit(0)
    else:
        print("\033[91mSYSTEM VERIFICATION FAILED.\033[0m")
        sys.exit(1)
