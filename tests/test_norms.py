"""
Test Historical Norms
Verifies if SecureAuditAgent picks correct norms for 2018 vs 2026.
"""
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from synapsa.agents.office_agent import SecureAuditAgent


class MockEngineNorms:
    """Mock LLM engine — implements the generate_chat interface expected by SecureAuditAgent."""

    def generate_chat(self, system_msg: str, user_msg: str) -> str:
        prompt = user_msg + system_msg
        if "2018" in prompt and "Brak not korygujących" not in prompt:
            return '{"status": "OK", "komentarz": "Użyto norm 2018. Faktura poprawna."}'
        if "2026" in prompt and "KSeF" in prompt:
            return '{"status": "OK", "komentarz": "Użyto norm 2026. KSeF obecny."}'
        return '{"status": "ERROR", "komentarz": "Złe normy."}'


def test_norms():
    print("TEST: Historical Norms Selection")

    # Setup agent with mock engine (bypass real LLM for logic check)
    agent = SecureAuditAgent(engine=MockEngineNorms())

    # 1. Test 2018
    print("--> Testing 2018 Invoice...")
    res_2018 = agent._generate_audit_plan("Sprawdź fakturę z datą 2018-05-12", ["invoice.pdf"])
    if "2018" in res_2018:
        print("✅ 2018 Norms Detected")
    else:
        print(f"❌ Failed 2018: {res_2018}")

    # 2. Test 2026
    print("--> Testing 2026 Invoice...")
    res_2026 = agent._generate_audit_plan("Faktura z 2026 roku", ["invoice.pdf"])
    if "2026" in res_2026:
        print("✅ 2026 Norms Detected")
    else:
        print(f"❌ Failed 2026: {res_2026}")


if __name__ == "__main__":
    test_norms()
