
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    print("🚀 Attempting to initialize SynapsaEngine...")
    from synapsa.engine import SynapsaEngine
    
    # Force init
    engine = SynapsaEngine()
    
    if hasattr(engine, "model"):
        print("✅ Engine initialized successfully. Model is present.")
    else:
        print("❌ Engine initialized but 'model' attribute is MISSING.")
        print(f"Initialized flag: {engine._initialized}")

except Exception as e:
    print(f"❌ CRITICAL ERROR during init: {e}")
    import traceback
    traceback.print_exc()
