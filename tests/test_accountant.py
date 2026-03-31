"""
Test Accountant Agent
Verifies the "Learning" and "Generation" capabilities.
"""
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from synapsa.agents.accountant_agent import AccountantAgent

class MockEngineAccountant:
    def generate(self, prompt, max_tokens=100):
        if "Profil Stylu" in prompt:
            return "Styl: Logo centralnie. Stopka z RODO. Termin płatności 14 dni."
        if "Wystaw fakturę" in prompt:
            return "FAKTURA VAT nr 1/2026\nSprzedawca: ...\n(Zgodnie ze stylem: Logo centralnie...)"
        return "Generic"

def test_accountant_learning():
    print("TEST: Accountant Learning")
    
    # Setup mock files
    os.makedirs("test_invoices", exist_ok=True)
    with open("test_invoices/wzor1.txt", "w") as f: f.write("Faktura Wzorcowa 1")
    
    agent = AccountantAgent(engine=MockEngineAccountant())
    
    # 1. Learn
    res = agent.learn_from_examples([os.path.abspath("test_invoices/wzor1.txt")])
    print(f"Result: {res}")
    
    if "Nauczyłam się" in res:
        print("✅ Learning Success")
    else:
        print("❌ Learning Failed")

    # 2. Generate
    print("\nTEST: Accountant Generation")
    doc = agent.generate_invoice("Usługa budowlana")
    print(f"Generated:\n{doc}")
    
    if "FAKTURA" in doc:
        print("✅ Generation Success")
    else:
        print("❌ Generation Failed")

    # Cleanup
    import shutil
    shutil.rmtree("test_invoices", ignore_errors=True)

if __name__ == "__main__":
    test_accountant_learning()
