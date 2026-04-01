"""
Test Historical Norms
Verifies that SecureAuditAgent selects the correct VAT/legal norms
based on invoice date (2018 vs 2026 regulatory regime).
"""
import os
import sys
import pytest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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


@pytest.fixture
def agent():
    """SecureAuditAgent wired with a deterministic mock engine."""
    return SecureAuditAgent(engine=MockEngineNorms())


class TestHistoricalNormsSelection:
    """Verifies that the agent applies the correct regulatory norms by year."""

    def test_2018_norms_detected(self, agent):
        """Invoice dated 2018 must trigger the 2018 regulatory norms."""
        result = agent._generate_audit_plan("Sprawdź fakturę z datą 2018-05-12", ["invoice.pdf"])
        assert "2018" in result, (
            f"Expected '2018' norms in response, got: {result!r}"
        )

    def test_2026_norms_detected(self, agent):
        """Invoice dated 2026 must trigger the 2026 regulatory norms (KSeF era)."""
        result = agent._generate_audit_plan("Faktura z 2026 roku", ["invoice.pdf"])
        assert "2026" in result, (
            f"Expected '2026' norms in response, got: {result!r}"
        )

    def test_result_is_string(self, agent):
        """Audit plan output must always be a string."""
        result = agent._generate_audit_plan("Faktura z 2026 roku", ["invoice.pdf"])
        assert isinstance(result, str), f"Expected str, got {type(result)}"

    def test_2018_does_not_return_error(self, agent):
        """2018 norms path should not return an ERROR status."""
        result = agent._generate_audit_plan("Sprawdź fakturę z datą 2018-05-12", ["invoice.pdf"])
        assert "ERROR" not in result, f"Unexpected ERROR in 2018 norms result: {result!r}"

    def test_2026_does_not_return_error(self, agent):
        """2026 norms path should not return an ERROR status."""
        result = agent._generate_audit_plan("Faktura z 2026 roku", ["invoice.pdf"])
        assert "ERROR" not in result, f"Unexpected ERROR in 2026 norms result: {result!r}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
