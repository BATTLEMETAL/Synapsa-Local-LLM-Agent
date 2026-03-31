"""
Symulacja "Secure Audit" (Biznesplan 2.0)
Sprawdza:
1. Czy pliki są kopiowane do `synapsa_workspace/safe_zone` (Izolacja).
2. Czy agent ponawia próbę po błędzie (Self-Correction).
"""
import os
import shutil
import sys
# Dodajemy katalog nadrzędny do ścieżki, żeby znaleźć moduł synapsa
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from synapsa.agents.office_agent import SecureAuditAgent

# Mock Engine
class MockEngineFailOnce:
    def __init__(self):
        self.attempts = 0
        
    def generate(self, prompt, max_tokens=100):
        self.attempts += 1
        print(f"   🤖 [AI] Generuję kod (Próba {self.attempts})...")
        
        if self.attempts == 1:
            # Próba 1: Błędny kod (np. zły import)
            return "```python\nimport nieistniejacy_modul\n```"
        else:
            # Próba 2: Poprawny kod (BEZ import os, bo jest zabroniony)
            return "```python\n# import os -> Zabronione\nprint('Raport Audytu: OK')\nwith open('audit_result.json', 'w') as f: f.write('{}')\n```"

def setup_test_files():
    os.makedirs("test_data", exist_ok=True)
    with open("test_data/faktura1.txt", "w") as f: f.write("Faktura 1: 100 PLN")
    with open("test_data/faktura2.txt", "w") as f: f.write("Faktura 2: 200 PLN")
    return [os.path.abspath("test_data/faktura1.txt"), os.path.abspath("test_data/faktura2.txt")]

def test_secure_audit():
    print("🚀 Rozpoczynam symulację Secure Audit...")
    
    # Setup
    files = setup_test_files()
    agent = SecureAuditAgent(engine=MockEngineFailOnce())
    
    # Run
    result = agent.process_audit("Sprawdź faktury", files)
    
    # Verify Isolation
    print("\n🔍 Weryfikacja Izolacji:")
    if result.get('workspace') and "synapsa_workspace" in result['workspace']:
        print("   ✅ Workspace jest w izolowanym folderze.")
        try:
            files_in_safe = os.listdir(result['workspace'])
            print(f"   ✅ Pliki w safe_zone: {files_in_safe}")
        except FileNotFoundError:
             print("   ❌ Nie znaleziono folderu workspace!")
    else:
        print(f"   ❌ Brak izolacji lub błąd! Result: {result}")

    # Verify Self-Correction
    print("\n🔍 Weryfikacja Self-Correction:")
    if agent.engine.attempts >= 2 and result['status'] == 'success':
        print("   ✅ Agent naprawił swój błąd w drugiej próbie.")
    else:
        print(f"   ❌ Błąd mechanizmu naprawczego. Próby: {agent.engine.attempts}")

    # Cleanup
    shutil.rmtree("test_data", ignore_errors=True)
    if result.get('workspace'):
        shutil.rmtree(result['workspace'], ignore_errors=True)

if __name__ == "__main__":
    test_secure_audit()
