
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.getcwd())

try:
    from synapsa.memory import ProjectMemory
    from synapsa.config import settings
    import chromadb
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

def check_knowledge():
    print("🧠 Checking Synapsa Memory...")
    
    try:
        mem = ProjectMemory()
        stats = mem.get_stats()
        
        if stats.get("status") != "active":
                         print(f"❌ Memory unavailable: {stats}")
                         return
                         
        count = stats.get("documents", 0)
        print(f"✅ Memory Connection Established.")
        print(f"📚 Total Documents in Memory: {count}")
        
        if count == 0:
            print("⚠️ Memory is empty! The system has no knowledge indexed yet.")
            return

        # Test Query
        query = "How does the Auditor work?"
        print(f"\n🔍 Querying: '{query}'...")
        results = mem.query(query, n_results=3)
        
        if results:
            print(f"✅ Found {len(results)} relevant fragments.")
            for i, res in enumerate(results):
                # ChromaDB results structure can be complex, robust print
                content = res.get('documents', [''])[0] if isinstance(res.get('documents'), list) else str(res)
                print(f"   {i+1}. {content[:100]}...")
        else:
            print("⚠️ No results found for query.")

    except Exception as e:
        print(f"❌ Memory Check Failed: {e}")

if __name__ == "__main__":
    check_knowledge()
