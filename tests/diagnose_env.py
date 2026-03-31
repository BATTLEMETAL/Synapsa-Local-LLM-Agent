import sys
import os
import importlib.util

print(f"Python Executable: {sys.executable}")
print(f"User Base: {os.path.expanduser('~')}")
print("\n--- SYS.PATH ---")
for p in sys.path:
    print(p)

print("\n--- PACKAGE CHECKS ---")
packages = ["sentence_transformers", "transformers", "chromadb"]
for pkg in packages:
    try:
        spec = importlib.util.find_spec(pkg)
        if spec:
            print(f"✅ Found {pkg}: {spec.origin}")
        else:
            print(f"❌ NOT FOUND: {pkg}")
    except Exception as e:
         print(f"⚠️ Error check {pkg}: {e}")

print("\n--- TRYING CRITICAL IMPORT ---")
try:
    from sentence_transformers import SentenceTransformer
    print("✅ Successfully imported SentenceTransformer")
except Exception as e:
    print(f"❌ Failed to import SentenceTransformer: {e}")
