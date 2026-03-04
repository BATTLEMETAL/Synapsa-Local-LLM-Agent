"""
Synapsa — Unified Application Launcher
Uruchamia serwer FastAPI na porcie 8000.
"""
import uvicorn
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Uruchamianie Synapsa Professional...")
    uvicorn.run("synapsa.api.app:app", host="0.0.0.0", port=8000, reload=True)