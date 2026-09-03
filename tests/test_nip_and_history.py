"""
Tests for NIP Validator and Invoice History modules.
"""
import os
import sys
import pytest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from synapsa.agents.nip_validator import (
    validate_nip,
    extract_nip,
    format_nip,
    validate_nip_from_field,
)


class TestNIPValidator:
    """Tests for Polish NIP validation."""

    def test_valid_nip_clean(self) -> None:
        """Known valid NIP."""
        ok, msg = validate_nip("5261040828")
        assert ok, f"Expected valid NIP, got: {msg}"

    def test_valid_nip_with_dashes(self) -> None:
        """NIP with dashes should be accepted."""
        ok, msg = validate_nip("526-104-08-28")
        assert ok, f"Expected valid NIP with dashes, got: {msg}"

    def test_invalid_nip_wrong_checksum(self) -> None:
        """NIP with wrong check digit should fail."""
        ok, msg = validate_nip("5261040829")  # last digit wrong
        assert not ok, "Expected invalid NIP (wrong checksum)"

    def test_invalid_nip_too_short(self) -> None:
        """NIP with fewer than 10 digits should fail."""
        ok, msg = validate_nip("12345")
        assert not ok
        assert "10 cyfr" in msg

    def test_invalid_nip_too_long(self) -> None:
        """NIP with more than 10 digits should fail."""
        ok, msg = validate_nip("12345678901")
        assert not ok
        assert "10 cyfr" in msg

    def test_empty_nip(self) -> None:
        ok, msg = validate_nip("")
        assert not ok
        assert "wymagany" in msg.lower()

    def test_extract_nip_from_text(self) -> None:
        text = "Firma X Sp. z o.o., NIP: 526-104-08-28, ul. Testowa 1"
        nip = extract_nip(text)
        assert nip == "5261040828"

    def test_extract_nip_no_nip_in_text(self) -> None:
        text = "Firma bez NIP, ul. Testowa 1"
        nip = extract_nip(text)
        assert nip is None

    def test_format_nip(self) -> None:
        result = format_nip("5261040828")
        assert result == "526-104-08-28"

    def test_validate_from_field_valid(self) -> None:
        field = "Firma X, NIP: 526-104-08-28"
        ok, msg, nip = validate_nip_from_field(field)
        assert ok
        assert nip == "5261040828"

    def test_validate_from_field_no_nip(self) -> None:
        """No NIP in field — should return True (just a warning, not blocking)."""
        field = "Firma X, ul. Testowa 1"
        ok, msg, nip = validate_nip_from_field(field)
        assert ok is True  # non-blocking
        assert nip is None

    def test_validate_from_field_invalid_nip(self) -> None:
        field = "Firma X, NIP: 5261040829"  # wrong checksum
        ok, msg, nip = validate_nip_from_field(field)
        assert not ok
        assert nip is not None


class TestInvoiceHistory:
    """Tests for SQLite invoice history."""

    def _make_result(self, nr: str = "FV/2026/001") -> dict:
        """Creates a minimal successful ZlecenieProcessor result dict."""
        return {
            "status": "success",
            "invoice_nr": nr,
            "invoice_date": "16.05.2026",
            "faktura_text": "FAKTURA VAT...",
            "calc": {
                "netto": 12000.0,
                "vat_rate": 23,
                "vat_kwota": 2760.0,
                "brutto": 14760.0,
                "mpp_required": False,
                "materialy_netto": 6600.0,
                "robocizna_netto": 5400.0,
                "metraz": 80.0,
                "jednostka": "m²",
                "cena_m2": 150.0,
                "pozycje": [{"ilosc": 80.0, "jednostka": "m²"}],
            },
            "parse": {
                "typ_pracy": "kostka brukowa",
                "metraz": 80.0,
                "cena_za_m2": 150.0,
                "jednostka": "m²",
                "vat_rate": 23,
                "material_ratio": 0.55,
                "raw": "test",
            },
            "kosztorys_text": "...",
            "error": None,
        }

    def test_save_and_retrieve(self, tmp_path) -> None:
        from synapsa.agents.invoice_history import InvoiceHistory
        db = InvoiceHistory(db_path=str(tmp_path / "test.db"))

        result = self._make_result("FV/2026/TEST01")
        saved = db.save(result, sprzedawca="Firma A", nabywca="Klient B")
        assert saved is True

        rows = db.get_all()
        assert len(rows) == 1
        assert rows[0]["nr"] == "FV/2026/TEST01"
        assert rows[0]["brutto"] == 14760.0
        assert rows[0]["sprzedawca"] == "Firma A"

    def test_duplicate_nr_ignored(self, tmp_path) -> None:
        from synapsa.agents.invoice_history import InvoiceHistory
        db = InvoiceHistory(db_path=str(tmp_path / "test.db"))

        r = self._make_result("FV/2026/TEST02")
        db.save(r)
        saved_again = db.save(r)  # same nr — should be ignored
        assert saved_again is False
        assert db.count() == 1

    def test_delete(self, tmp_path) -> None:
        from synapsa.agents.invoice_history import InvoiceHistory
        db = InvoiceHistory(db_path=str(tmp_path / "test.db"))

        db.save(self._make_result("FV/2026/DEL01"))
        assert db.count() == 1
        db.delete("FV/2026/DEL01")
        assert db.count() == 0

    def test_stats(self, tmp_path) -> None:
        from synapsa.agents.invoice_history import InvoiceHistory
        db = InvoiceHistory(db_path=str(tmp_path / "test.db"))

        db.save(self._make_result("FV/2026/S01"))
        db.save(self._make_result("FV/2026/S02"))

        stats = db.get_stats()
        assert stats["count"] == 2
        assert stats["total_brutto"] == pytest.approx(14760.0 * 2)
        assert stats["mpp_count"] == 0

    def test_failed_result_not_saved(self, tmp_path) -> None:
        from synapsa.agents.invoice_history import InvoiceHistory
        db = InvoiceHistory(db_path=str(tmp_path / "test.db"))

        bad_result = {"status": "error", "error": "Brak ceny"}
        saved = db.save(bad_result)
        assert saved is False
        assert db.count() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
