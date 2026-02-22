"""
Unit tests for the script generator module.
"""

import unittest
from unittest.mock import patch

from src.scraper import RupiahData, GoldData
from src.summarizer import RupiahAnalysis, GoldAnalysis
from src.script_generator import ScriptGenerator


class TestScriptGenerator(unittest.TestCase):
    """Test script generation functionality."""

    def setUp(self):
        self.generator = ScriptGenerator()

    def test_format_number_indonesian(self):
        """Test number formatting with Indonesian separators."""
        self.assertEqual(self.generator._format_number(16000), "16.000")
        self.assertEqual(self.generator._format_number(1000000), "1.000.000")

    def test_format_number_with_decimals(self):
        """Test number formatting with decimal places."""
        self.assertEqual(self.generator._format_number(16000.5, 2), "16.000,50")

    def test_format_number_none(self):
        """Test formatting None value."""
        self.assertEqual(self.generator._format_number(None), "-")

    def test_get_current_day_date(self):
        """Test day and date retrieval."""
        day, date = self.generator._get_current_day_date()
        # Should return Indonesian day name
        valid_days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        self.assertIn(day, valid_days)


class TestRupiahScriptGeneration(unittest.TestCase):
    """Test Rupiah script generation."""

    def setUp(self):
        self.generator = ScriptGenerator()
        self.rupiah_data = RupiahData(
            title="Rupiah Melemah Terhadap Dolar AS",
            opening_rate=16000.0,
            current_rate=16100.0,
            time_wib="10:00",
            percentage_change=-0.62,
            trend="melemah",
            asian_currencies=[
                {"name": "Yen", "change_pct": 0.2},
                {"name": "Won", "change_pct": -0.3},
            ],
            content="Test content about rupiah",
        )
        self.rupiah_analysis = RupiahAnalysis(
            external_analysis="Indeks dolar AS menguat hari ini.",
            asian_currencies_text="Yen (+0.20%), Won (-0.30%)",
            global_domestic_analysis="Bank Indonesia menjaga stabilitas.",
            forecast_range="Rp 16.050 - Rp 16.150/US$",
        )

    def test_generate_rupiah_script_structure(self):
        """Test Rupiah script has required sections."""
        script = self.generator.generate_rupiah_script(
            self.rupiah_data, self.rupiah_analysis
        )

        # Check required sections exist
        self.assertIn("JUDUL :", script)
        self.assertIn("NILAI TUKAR RUPIAH", script)
        self.assertIn("NILAI TUKAR MATA UANG ASIA", script)
        self.assertIn("PERKIRAAN PELEMAHAN RUPIAH", script)

    def test_generate_rupiah_script_contains_title(self):
        """Test Rupiah script contains the title."""
        script = self.generator.generate_rupiah_script(
            self.rupiah_data, self.rupiah_analysis
        )
        self.assertIn(self.rupiah_data.title, script)

    def test_generate_rupiah_script_contains_rate(self):
        """Test Rupiah script contains exchange rate."""
        script = self.generator.generate_rupiah_script(
            self.rupiah_data, self.rupiah_analysis
        )
        self.assertIn("16.100", script)

    def test_generate_rupiah_script_contains_trend(self):
        """Test Rupiah script contains trend word."""
        script = self.generator.generate_rupiah_script(
            self.rupiah_data, self.rupiah_analysis
        )
        self.assertIn("melemah", script.lower())


class TestGoldScriptGeneration(unittest.TestCase):
    """Test Gold script generation."""

    def setUp(self):
        self.generator = ScriptGenerator()
        self.gold_data = GoldData(
            title="Harga Emas Antam Naik Hari Ini",
            antam_price=1000000.0,
            antam_change=5000.0,
            antam_trend="naik",
            buyback_price=900000.0,
            buyback_change=-4500.0,  # Different trend from Antam
            global_gold_usd=2000.0,
            global_gold_change_pct=0.5,
            date="21 Februari 2026",
            content="Test content about gold",
        )
        self.gold_analysis = GoldAnalysis(
            global_correlation="Emas Antam mengikuti tren global.",
            forecast_range_usd="US$ 1.980 - US$ 2.020/troy ons",
            forecast_range_idr="Rp 1.040.000 - Rp 1.060.000/gram",
            price_catalysts="Faktor geopolitik mendorong harga.",
        )

    def test_generate_gold_script_structure(self):
        """Test Gold script has required sections."""
        script = self.generator.generate_gold_script(
            self.gold_data, self.gold_analysis
        )

        # Check required sections exist
        self.assertIn("JUDUL :", script)
        self.assertIn("HARGA EMAS ANTAM", script)
        self.assertIn("HARGA BUYBACK EMAS ANTAM", script)
        self.assertIn("HARGA EMAS DUNIA", script)
        self.assertIn("PERKIRAAN KENAIKAN HARGA EMAS DUNIA", script)

    def test_generate_gold_script_simplified_title(self):
        """Test Gold script uses simplified title format."""
        script = self.generator.generate_gold_script(
            self.gold_data, self.gold_analysis
        )
        self.assertIn("JUDUL : EMAS ANTAM NAIK RP5.000/GRAM, HARI INI", script)

    def test_generate_gold_script_contains_price(self):
        """Test Gold script contains Antam price."""
        script = self.generator.generate_gold_script(
            self.gold_data, self.gold_analysis
        )
        self.assertIn("1.000.000", script)

    def test_generate_gold_script_contains_trend(self):
        """Test Gold script contains trend word."""
        script = self.generator.generate_gold_script(
            self.gold_data, self.gold_analysis
        )
        self.assertIn("kembali naik", script)

    def test_generate_gold_script_buyback_independent_trend(self):
        """Test buyback trend is calculated independently from Antam."""
        script = self.generator.generate_gold_script(
            self.gold_data, self.gold_analysis
        )
        # Antam is naik, but buyback_change is negative so should be turun
        self.assertIn("Turun Rp4.500/gram", script)

    def test_generate_gold_script_global_gold_format(self):
        """Test global gold price is formatted correctly with decimal."""
        script = self.generator.generate_gold_script(
            self.gold_data, self.gold_analysis
        )
        # Should have decimal format like "US$ 2.000,0"
        self.assertIn("US$ 2.000,0/troy ons", script)

    def test_generate_gold_script_percentage_format(self):
        """Test percentage uses Indonesian format with comma."""
        script = self.generator.generate_gold_script(
            self.gold_data, self.gold_analysis
        )
        # Should use comma as decimal separator: "0,50%"
        self.assertIn("0,50%", script)

    def test_generate_gold_script_with_rupiah_rate(self):
        """Test Gold script generation with custom rupiah rate."""
        script = self.generator.generate_gold_script(
            self.gold_data, self.gold_analysis, rupiah_rate=16500.0
        )
        self.assertIsNotNone(script)

    def test_generate_gold_title_helper(self):
        """Test the gold title helper method."""
        title = self.generator._generate_gold_title("naik", 28000)
        self.assertEqual(title, "EMAS ANTAM NAIK RP28.000/GRAM, HARI INI")

        title = self.generator._generate_gold_title("turun", 15000)
        self.assertEqual(title, "EMAS ANTAM TURUN RP15.000/GRAM, HARI INI")

        title = self.generator._generate_gold_title("stagnan", 0)
        self.assertEqual(title, "EMAS ANTAM STAGNAN RP0/GRAM, HARI INI")

    def test_generate_gold_script_stagnan_no_change_line(self):
        """Test that stagnan prices don't show change line."""
        gold_data = GoldData(
            title="Harga Emas Antam Stagnan",
            antam_price=2944000.0,
            antam_change=0.0,
            antam_trend="stagnan",
            buyback_price=2649600.0,
            buyback_change=0.0,
            global_gold_usd=2000.0,
            global_gold_change_pct=0.0,
            date="20 Februari 2026",
            content="Test content",
        )
        gold_analysis = GoldAnalysis(
            global_correlation="Korelasi text.",
            forecast_range_usd="US$ 1.980 - US$ 2.020/troy ons",
            forecast_range_idr="Rp 1.040.000 - Rp 1.060.000/gram",
            price_catalysts="Catalyst text.",
        )

        script = self.generator.generate_gold_script(gold_data, gold_analysis)

        # Should NOT contain "Stagnan Rp 0/gram"
        self.assertNotIn("Stagnan Rp 0", script)
        self.assertNotIn("stagnan Rp 0", script.lower())

        # Should only show the price, not the change line
        self.assertIn("Rp 2.944.000/gram.", script)
        self.assertIn("Rp 2.649.600/gram.", script)

    def test_generate_gold_script_naik_shows_change_line(self):
        """Test that naik prices show change line."""
        gold_data = GoldData(
            title="Harga Emas Antam Naik",
            antam_price=2944000.0,
            antam_change=28000.0,
            antam_trend="naik",
            buyback_price=2725000.0,
            buyback_change=31000.0,
            global_gold_usd=2000.0,
            global_gold_change_pct=0.5,
            date="20 Februari 2026",
            content="Test content",
        )
        gold_analysis = GoldAnalysis(
            global_correlation="Korelasi text.",
            forecast_range_usd="US$ 1.980 - US$ 2.020/troy ons",
            forecast_range_idr="Rp 1.040.000 - Rp 1.060.000/gram",
            price_catalysts="Catalyst text.",
        )

        script = self.generator.generate_gold_script(gold_data, gold_analysis)

        # Should contain the change line
        self.assertIn("Naik Rp28.000/gram dari hari sebelumnya", script)
        self.assertIn("Naik Rp31.000/gram dari sebelumnya", script)

    def test_generate_gold_script_turun_shows_change_line(self):
        """Test that turun prices show change line."""
        gold_data = GoldData(
            title="Harga Emas Antam Turun",
            antam_price=2944000.0,
            antam_change=-15000.0,
            antam_trend="turun",
            buyback_price=2649600.0,
            buyback_change=-20000.0,
            global_gold_usd=2000.0,
            global_gold_change_pct=-0.3,
            date="20 Februari 2026",
            content="Test content",
        )
        gold_analysis = GoldAnalysis(
            global_correlation="Korelasi text.",
            forecast_range_usd="US$ 1.980 - US$ 2.020/troy ons",
            forecast_range_idr="Rp 1.040.000 - Rp 1.060.000/gram",
            price_catalysts="Catalyst text.",
        )

        script = self.generator.generate_gold_script(gold_data, gold_analysis)

        # Should contain the change line with Turun
        self.assertIn("Turun Rp15.000/gram dari hari sebelumnya", script)
        self.assertIn("Turun Rp20.000/gram dari sebelumnya", script)


class TestTelegramFormatting(unittest.TestCase):
    """Test Telegram message formatting."""

    def setUp(self):
        self.generator = ScriptGenerator()

    def test_format_for_telegram_adds_header(self):
        """Test Telegram formatting adds header."""
        script = "Test script content"
        formatted = self.generator.format_for_telegram(script, "Rupiah")

        self.assertIn("📊", formatted)
        self.assertIn("*SCRIPT RUPIAH*", formatted)

    def test_format_for_telegram_adds_footer(self):
        """Test Telegram formatting adds footer."""
        script = "Test script content"
        formatted = self.generator.format_for_telegram(script, "Gold")

        self.assertIn("BloombergTechnoz.com", formatted)

    def test_format_for_telegram_escapes_special_chars(self):
        """Test Telegram formatting escapes special characters."""
        script = "Test_with*special[chars]"
        formatted = self.generator.format_for_telegram(script, "Rupiah")

        self.assertIn("\\_", formatted)
        self.assertIn("\\*", formatted)


class TestScriptWithMissingData(unittest.TestCase):
    """Test script generation with missing data (fallback behavior)."""

    def setUp(self):
        self.generator = ScriptGenerator()

    def test_rupiah_script_with_none_values(self):
        """Test Rupiah script handles None values gracefully."""
        rupiah_data = RupiahData(
            title="Test Title",
            opening_rate=None,
            current_rate=None,
            time_wib=None,
            percentage_change=None,
            trend=None,
            asian_currencies=[],
            content="Test",
        )
        rupiah_analysis = RupiahAnalysis(
            external_analysis="Analysis text.",
            asian_currencies_text="No data",
            global_domestic_analysis="More analysis.",
            forecast_range="Rp 16.000 - Rp 16.200",
        )

        script = self.generator.generate_rupiah_script(rupiah_data, rupiah_analysis)
        self.assertIsNotNone(script)
        self.assertIn("JUDUL :", script)

    def test_gold_script_with_none_values(self):
        """Test Gold script handles None values gracefully."""
        gold_data = GoldData(
            title="Test Title",
            antam_price=None,
            antam_change=None,
            antam_trend=None,
            buyback_price=None,
            buyback_change=None,
            global_gold_usd=None,
            global_gold_change_pct=None,
            date="21 Februari 2026",
            content="Test",
        )
        gold_analysis = GoldAnalysis(
            global_correlation="Correlation text.",
            forecast_range_usd="US$ 1.900 - US$ 2.100",
            forecast_range_idr="Rp 1.000.000 - Rp 1.100.000",
            price_catalysts="Catalyst text.",
        )

        script = self.generator.generate_gold_script(gold_data, gold_analysis)
        self.assertIsNotNone(script)
        self.assertIn("JUDUL :", script)


if __name__ == "__main__":
    unittest.main()
