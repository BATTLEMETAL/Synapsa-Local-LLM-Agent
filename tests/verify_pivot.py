"""
Test weryfikujący (Pivot Verification)
Sprawdza:
1. Czy SafetyGuard blokuje niebezpieczny kod.
2. Czy OfficeAgent potrafi (teoretycznie) przetworzyć zadanie.
"""
import os
from synapsa.core.safety import validate_code
from synapsa.agents.office_agent import OfficeAgent

def test_safety_guard():
    print("🛡️  Test Safety Guard...")
    
    safe_code = "import pandas as pd\ndf = pd.DataFrame()\nprint(df)"
    unsafe_code = "import os\nos.system('echo hack')"
    
    ok1, _ = validate_code(safe_code)
    ok2, msg = validate_code(unsafe_code)
    
    if ok1 and not ok2:
        print("   ✅ Guard działa poprawnie (Zablokował 'os').")
    else:
        print(f"   ❌ Awaria Guarda! Safe={ok1}, Unsafe={ok2}")

def test_office_agent_mock():
    print("\n🕵️  Test Office Agent (Mock Engine)...")
    
    # Mockujemy silnik, żeby nie ładować 7GB modelu do testu unitowego
    class MockEngine:
        def generate(self, prompt, max_tokens=100):
            return '''
            ```python
            import pandas as pd
            print("Symulacja obliczeń...")
            ```
            '''
            
    agent = OfficeAgent(engine=MockEngine())
    res = agent.process_task("Policz sumę")
    
    if res['status'] == 'success' and "Symulacja" in res['execution_output']:
         print("   ✅ Agent wygenerował i wykonał kod.")
    else:
         print(f"   ❌ Błąd agenta: {res}")

if __name__ == "__main__":
    test_safety_guard()
    test_office_agent_mock()
