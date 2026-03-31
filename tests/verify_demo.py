"""
Verify Demo Script
Automated test for Construction Demo scenarios.
"""
import os
import sys
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from synapsa.agents.office_agent import SecureAuditAgent
from synapsa.agents.construction_agent import ConstructionChatAgent

# Mock Engine for consistent testing
class MockEngineConstruction:
    def __init__(self):
        self.attempts = 0
    
    def generate(self, prompt, max_tokens=100, reasoning=False):
        # Handle Audit Prompt (returns JSON code)
        if "Secure Audit" in prompt:
             return "```python\n# Mock Code\nprint('Raport: OK')\nwith open('audit_result.json', 'w') as f: f.write('{}')\n```"
        
        # Handle Construction Chat Prompt
        if "Inżynier Synapsa" in prompt:
            return "Oto wycena:\n- Robocizna: 1000zł\n- Materiały: 500zł\nRazem: 1500zł."
            
        return f"Generic Response (Prompt was: {prompt[:20]}...)"

def test_audit_scenario():
    print("TEST: Audit Scenario")
    # Setup
    os.makedirs("test_demo_docs", exist_ok=True)
    with open("test_demo_docs/faktura.txt", "w") as f: f.write("Faktura Testowa")
    
    agent = SecureAuditAgent(engine=MockEngineConstruction())
    result = agent.process_audit("Sprawdź fakturę", [os.path.abspath("test_demo_docs/faktura.txt")])
    
    if result['status'] == 'success':
        print("✅ Audit Success")
    else:
        print(f"❌ Audit Failed: {result}")
    
    shutil.rmtree("test_demo_docs", ignore_errors=True)
    if result.get('workspace'):
        shutil.rmtree(result['workspace'], ignore_errors=True)

def test_chat_scenario():
    print("\nTEST: Chat Scenario")
    agent = ConstructionChatAgent(engine=MockEngineConstruction())
    response = agent.chat("Ile kosztuje remont?")
    
    if "Oto wycena" in response:
        print("✅ Chat Success")
    else:
        print(f"❌ Chat Failed: {response}")

if __name__ == "__main__":
    test_audit_scenario()
    test_chat_scenario()
