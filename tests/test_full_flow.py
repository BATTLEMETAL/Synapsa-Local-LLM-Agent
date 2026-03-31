import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_full_flow():
    print("🚀 Starting End-to-End System Test...")
    
    # 1. Initialize State
    print("\n[1/4] Initializing Global State...")
    try:
        from synapsa.api.state import state
        from synapsa.memory import ProjectMemory
        from synapsa.agents.coder import InteractiveCoder
        from synapsa.agents.auditor import HybridAuditor
        
        state.memory = ProjectMemory()
        if not state.memory.available:
            print("⚠️ Memory not available (likely missing ChromaDB or sentence-transformers).")
        else:
            print(f"✅ Memory active. Documents: {state.memory.get_stats().get('documents', 0)}")
            
        # Initialize Coder (Lazy load engine)
        state.coder = InteractiveCoder()
        print("✅ Coder Agent initialized.")
        
        state.auditor = HybridAuditor()
        print("✅ Auditor initialized.")
        
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        return

    # 2. Test Memory Indexing (Mock)
    print("\n[2/4] Testing Memory Indexing...")
    try:
        if state.memory.available:
            # Index a dummy file
            dummy_path = os.path.join(os.getcwd(), "tests")
            res = state.memory.index_project(dummy_path)
            print(f"✅ Indexing result: {res}")
            
            # Query
            q = state.memory.query("verification script")
            print(f"✅ Query result: Found {len(q)} matches.")
        else:
            print("⏩ Skipping memory test (unavailable).")
    except Exception as e:
        print(f"❌ Memory Test Failed: {e}")

    # 3. Test Interactive Coder (Mock Generation)
    print("\n[3/4] Testing Interactive Coder (Dry Run)...")
    try:
        # We don't want to load the full 7B model if we can avoid it, or we rely on CPU fallback
        # This will test if the generate method runs without crashing
        
        # Inject a mock engine to avoid loading 14GB model
        class MockEngine:
            def generate(self, prompt, max_tokens, reasoning=False):
                return "<thinking>\nMock reasoning...\n</thinking>\n```python\nprint('Hello World')\n```"
            def smart_generate(self, prompt, max_tokens):
                return "print('Hello World')"
            def is_ready(self): return True
            
        state.coder.engine = MockEngine()
        print("ℹ️ Injected Mock Engine for safety.")
        
        response = state.coder.generate("Write a hello world script")
        if response['status'] == 'success':
            print("✅ Coder generation successful.")
            print(f"   Code: {response['code']}")
        else:
            print(f"❌ Coder generation failed: {response.get('message')}")
            
    except Exception as e:
        print(f"❌ Coder Test Failed: {e}")

    # 4. Test Auditor
    print("\n[4/4] Testing Auditor...")
    try:
        audit_res = state.auditor.audit("def foo(): pass", "test.py")
        # Auditor might fail if metrics/AST parsing fails, but let's see
        print(f"✅ Auditor result keys: {list(audit_res.keys())}")
    except Exception as e:
        print(f"❌ Auditor Test Failed: {e}")

    print("\n✅ End-to-End Test Finished.")

if __name__ == "__main__":
    test_full_flow()
