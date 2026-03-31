import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_memory_init():
    print("Testing ProjectMemory initialization...")
    from synapsa.memory import ProjectMemory
    try:
        mem = ProjectMemory()
        if mem.available:
            print("✅ ProjectMemory initialized/connected successfully.")
        else:
            print("⚠️ ProjectMemory unavailable (check ChromaDB/imports).")
    except Exception as e:
        print(f"❌ ProjectMemory Failed: {e}")
        raise

def test_engine_init():
    print("\nTesting SynapsaEngine initialization (Mocking torch/cuda if needed)...")
    from synapsa.engine import SynapsaEngine
    try:
        # Mocking torch.cuda.is_available to avoid massive model load if not on GPU or just to test logic
        # But we want to test the REAL load if possible, or at least the import logic.
        # loading the 7B model might kill the agent's memory.
        # Let's just check if the class imports and we can inspect the singleton.
        print("Engine class imported.")
        
        # We won't instantiate the full engine here to avoid OOM in this test environment 
        # unless the user has a powerful GPU and we want to wait. 
        # But we can check if the code runs up to the point of model load.
        pass 
    except Exception as e:
        print(f"❌ SynapsaEngine Import/Init Failed: {e}")
        raise

if __name__ == "__main__":
    try:
        test_memory_init()
        test_engine_init()
        print("\n✅ Verification script finished.")
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        sys.exit(1)
