"""
Synapsa — Unit Tests for Business Logic
Tests the core parsing, calculation, and validation logic WITHOUT requiring the AI model.
"""
import json
import os
import sys
import pytest

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from synapsa.agents.zlecenie_processor import (
    ZlecenieParser,
    ZlecenieCalculator,
    _next_invoice_number,
)


# ---------------------------------------------------------------------------
# ZlecenieParser Tests
# ---------------------------------------------------------------------------

class TestZlecenieParser:
    """Tests for the natural-language order parser."""

    def setup_method(self) -> None:
        self.parser = ZlecenieParser()

    # -- Work type detection --

    def test_detects_work_type_kostka(self) -> None:
        result = self.parser.parse("Nowe zlecenie: budowanie kostki brukowej 80m2, cena 150 PLN/m2")
        # Parser detects "budowa" as the work type from "budowanie"
        assert any(
            kw in result["typ_pracy"].lower()
            for kw in ("kostka", "bruk", "budow")
        )

    def test_detects_work_type_ocieplenie(self) -> None:
        result = self.parser.parse("Ocieplenie budynku styropianem 15cm, 200m2, stawka 120 zł za m")
        assert "ocieplen" in result["typ_pracy"].lower() or "styropian" in result["typ_pracy"].lower()

    # -- Area extraction --

    def test_extracts_area_m2(self) -> None:
        result = self.parser.parse("kostka brukowa 80m2, cena 150 PLN")
        assert result["metraz"] == 80.0

    def test_extracts_area_with_space(self) -> None:
        result = self.parser.parse("ocieplenie 200 m2 za 120 zł")
        assert result["metraz"] == 200.0

    def test_extracts_area_mb(self) -> None:
        result = self.parser.parse("ogrodzenie 50mb stawka 300 PLN")
        assert result["metraz"] == 50.0

    # -- Price extraction --

    def test_extracts_price_pln(self) -> None:
        result = self.parser.parse("kostka brukowa 80m2, cena 150 PLN za m2")
        assert result["cena_za_m2"] == 150.0

    def test_extracts_price_zl(self) -> None:
        result = self.parser.parse("tynkowanie 100m2 za 45 zł za m")
        assert result["cena_za_m2"] == 45.0

    def test_ignores_thickness_as_price(self) -> None:
        """15cm should NOT be parsed as a price."""
        result = self.parser.parse("ocieplenie styropianem 15cm, 200m2, cena 120 PLN/m2")
        assert result["cena_za_m2"] == 120.0

    # -- VAT detection --

    def test_vat_8_for_renovation(self) -> None:
        result = self.parser.parse("remont łazienki 20m2, cena 200 PLN")
        assert result["vat_rate"] == 8

    def test_vat_23_for_new_construction(self) -> None:
        result = self.parser.parse("budowa nowego ogrodzenia 50mb, cena 300 PLN")
        assert result["vat_rate"] == 23


# ---------------------------------------------------------------------------
# ZlecenieCalculator Tests
# ---------------------------------------------------------------------------

class TestZlecenieCalculator:
    """Tests for the cost estimation calculator."""

    def setup_method(self) -> None:
        self.calc = ZlecenieCalculator()

    def test_basic_calculation(self) -> None:
        parsed = {
            "typ_pracy": "kostka brukowa",
            "metraz": 100.0,
            "cena_za_m2": 150.0,
            "jednostka": "m²",
            "vat_rate": 23,
            "material_ratio": 0.55,
        }
        result = self.calc.calculate(parsed)
        assert result["netto"] == 15000.0
        assert result["vat_rate"] == 23
        assert result["vat_kwota"] == 3450.0
        assert result["brutto"] == 18450.0
        assert result["materialy_netto"] == 8250.0
        assert result["robocizna_netto"] == 6750.0

    def test_mpp_required_above_15000(self) -> None:
        """Mechanizm podzielonej płatności required for brutto >= 15000 PLN."""
        parsed = {
            "typ_pracy": "kostka brukowa",
            "metraz": 100.0,
            "cena_za_m2": 150.0,
            "jednostka": "m²",
            "vat_rate": 23,
            "material_ratio": 0.55,
        }
        result = self.calc.calculate(parsed)
        assert result["mpp_required"] is True

    def test_mpp_not_required_below_15000(self) -> None:
        parsed = {
            "typ_pracy": "tynkowanie",
            "metraz": 20.0,
            "cena_za_m2": 50.0,
            "jednostka": "m²",
            "vat_rate": 23,
            "material_ratio": 0.35,
        }
        result = self.calc.calculate(parsed)
        assert result["brutto"] < 15000
        assert result["mpp_required"] is False

    def test_komplet_pricing(self) -> None:
        """For 'komplet' unit, the price is the total, not per-m2."""
        parsed = {
            "typ_pracy": "instalacja elektryczna",
            "metraz": 0.0,
            "cena_za_m2": 25000.0,
            "jednostka": "komplet",
            "vat_rate": 23,
            "material_ratio": 0.40,
        }
        result = self.calc.calculate(parsed)
        assert result["netto"] == 25000.0

    def test_zero_area_zero_price(self) -> None:
        parsed = {
            "typ_pracy": "ogólne",
            "metraz": 0.0,
            "cena_za_m2": 0.0,
            "jednostka": "m²",
            "vat_rate": 23,
            "material_ratio": 0.50,
        }
        result = self.calc.calculate(parsed)
        assert result["netto"] == 0.0
        assert result["brutto"] == 0.0


# ---------------------------------------------------------------------------
# VAT Norms Tests
# ---------------------------------------------------------------------------

class TestVatNorms:
    """Tests for the VAT norms knowledge base."""

    def test_vat_norms_file_exists(self) -> None:
        norms_path = os.path.join(
            os.path.dirname(__file__), "..", "synapsa", "knowledge", "vat_norms.json"
        )
        assert os.path.exists(norms_path), f"VAT norms file not found at {norms_path}"

    def test_vat_norms_valid_json(self) -> None:
        norms_path = os.path.join(
            os.path.dirname(__file__), "..", "synapsa", "knowledge", "vat_norms.json"
        )
        if os.path.exists(norms_path):
            with open(norms_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, (dict, list)), "VAT norms must be a dict or list"


# ---------------------------------------------------------------------------
# Integration-style: Parser + Calculator together
# ---------------------------------------------------------------------------

class TestParserCalculatorIntegration:
    """Tests the full parse -> calculate pipeline."""

    def setup_method(self) -> None:
        self.parser = ZlecenieParser()
        self.calc = ZlecenieCalculator()

    def test_full_pipeline_kostka(self) -> None:
        parsed = self.parser.parse("kostka brukowa 80m2, cena 150 PLN za metr")
        result = self.calc.calculate(parsed)

        assert result["metraz"] == 80.0
        assert result["cena_m2"] == 150.0
        assert result["netto"] == 12000.0
        assert result["brutto"] > result["netto"]

    def test_full_pipeline_remont(self) -> None:
        parsed = self.parser.parse("remont łazienki 15m2, stawka 200 zł")
        result = self.calc.calculate(parsed)

        assert result["vat_rate"] == 8  # renovation = 8% VAT
        assert result["netto"] == 3000.0
        expected_vat = 3000.0 * 0.08
        assert result["vat_kwota"] == expected_vat


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
