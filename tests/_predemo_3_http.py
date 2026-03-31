"""Test 3: HTTP serwer + pliki demo"""
import sys, os, glob, urllib.request

all_ok = True
print("\n[HTTP & PLIKI DEMO]")

# HTTP
try:
    resp = urllib.request.urlopen('http://localhost:8501', timeout=5)
    code = resp.getcode()
    print(f"  [OK] Streamlit HTTP {code} — serwer dziala na localhost:8501")
except Exception as e:
    print(f"  [XX] Streamlit offline: {e}")
    all_ok = False

# Pliki demo
demo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'demo_docs'))
fs = sorted(glob.glob(os.path.join(demo_dir, 'FV_*.txt')))
if len(fs) >= 6:
    print(f"  [OK] demo_docs/ — {len(fs)} faktur testowych:")
else:
    print(f"  [XX] demo_docs/ — za malo plikow: {len(fs)} (oczekiwano >=6)")
    all_ok = False

for f in fs:
    sz = os.path.getsize(f)
    print(f"       {os.path.basename(f):<50} ({sz:>5} B)")

print()
print("WYNIK:", "HTTP I PLIKI DEMO OK" if all_ok else "PROBLEMY Z SERWEREM LUB PLIKAMI!")
sys.exit(0 if all_ok else 1)
