"""
Unit tests for the scraper module.
"""

import unittest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from src.scraper import (
    BloombergTechnozScraper,
    RupiahData,
    GoldData,
)


class TestNumberExtraction(unittest.TestCase):
    """Test number extraction methods."""

    def setUp(self):
        self.scraper = BloombergTechnozScraper()

    def test_extract_number_basic(self):
        """Test basic number extraction."""
        self.assertEqual(self.scraper._extract_number("16000"), 16000.0)
        self.assertEqual(self.scraper._extract_number("Rp 16.000"), 16000.0)

    def test_extract_number_none(self):
        """Test extraction with None input."""
        self.assertIsNone(self.scraper._extract_number(None))

    def test_extract_percentage(self):
        """Test percentage extraction."""
        self.assertEqual(self.scraper._extract_percentage("+0.5%"), 0.5)
        self.assertEqual(self.scraper._extract_percentage("-1.2%"), -1.2)

    def test_extract_percentage_none(self):
        """Test percentage extraction with None."""
        self.assertIsNone(self.scraper._extract_percentage(None))

    def test_determine_trend_positive(self):
        """Test trend determination for positive change."""
        self.assertEqual(self.scraper._determine_trend(0.5), "menguat")

    def test_determine_trend_negative(self):
        """Test trend determination for negative change."""
        self.assertEqual(self.scraper._determine_trend(-0.5), "melemah")

    def test_determine_trend_zero(self):
        """Test trend determination for zero change."""
        self.assertEqual(self.scraper._determine_trend(0), "stagnan")

    def test_determine_gold_trend_naik(self):
        """Test gold trend for price increase."""
        self.assertEqual(self.scraper._determine_gold_trend(5000), "naik")

    def test_determine_gold_trend_turun(self):
        """Test gold trend for price decrease."""
        self.assertEqual(self.scraper._determine_gold_trend(-5000), "turun")


class TestRupiahParsing(unittest.TestCase):
    """Test Rupiah content parsing."""

    def setUp(self):
        self.scraper = BloombergTechnozScraper()

    def test_parse_rupiah_opening_rate(self):
        """Test parsing opening rate from content."""
        content = "Pada pembukaan, rupiah diperdagangkan di level 16.000/US$"
        result = self.scraper._parse_rupiah_from_content(content)
        self.assertEqual(result["opening_rate"], 16000.0)

    def test_parse_rupiah_current_rate(self):
        """Test parsing current rate from content."""
        content = "rupiah bergerak ke angka 16.100/US$"
        result = self.scraper._parse_rupiah_from_content(content)
        self.assertEqual(result["current_rate"], 16100.0)

    def test_parse_rupiah_time(self):
        """Test parsing time from content."""
        content = "pada pukul 10:30 WIB"
        result = self.scraper._parse_rupiah_from_content(content)
        self.assertEqual(result["time_wib"], "10:30")

    def test_parse_rupiah_percentage(self):
        """Test parsing percentage change from content."""
        content = "melemah 0.5% dari sebelumnya"
        result = self.scraper._parse_rupiah_from_content(content)
        self.assertEqual(result["percentage_change"], -0.5)


class TestGoldParsing(unittest.TestCase):
    """Test Gold content parsing."""

    def setUp(self):
        self.scraper = BloombergTechnozScraper()

    def test_parse_gold_antam_price(self):
        """Test parsing Antam gold price from content."""
        content = "Harga emas Antam Rp 1.000.000/gram"
        result = self.scraper._parse_gold_from_content(content)
        self.assertEqual(result["antam_price"], 1000000.0)

    def test_parse_gold_antam_change_naik(self):
        """Test parsing Antam price increase."""
        content = "naik Rp 5.000/gram"
        result = self.scraper._parse_gold_from_content(content)
        self.assertEqual(result["antam_change"], 5000.0)

    def test_parse_gold_antam_change_turun(self):
        """Test parsing Antam price decrease."""
        content = "turun Rp 5.000/gram"
        result = self.scraper._parse_gold_from_content(content)
        self.assertEqual(result["antam_change"], -5000.0)

    def test_parse_gold_buyback(self):
        """Test parsing buyback price from content."""
        content = "harga buyback Rp 900.000/gram"
        result = self.scraper._parse_gold_from_content(content)
        self.assertEqual(result["buyback_price"], 900000.0)


class TestScraperSelectors(unittest.TestCase):
    """Test scraper selector fallbacks."""

    def setUp(self):
        self.scraper = BloombergTechnozScraper()

    def test_extract_text_first_selector(self):
        """Test text extraction with first selector matching."""
        html = """
        <html>
            <body>
                <h1 class="entry-title">Test Title</h1>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        selectors = ["h1.entry-title", "h1"]
        result = self.scraper._extract_text(soup, selectors)
        self.assertEqual(result, "Test Title")

    def test_extract_text_fallback_selector(self):
        """Test text extraction with fallback selector."""
        html = """
        <html>
            <body>
                <h1>Fallback Title</h1>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        selectors = ["h1.nonexistent", "h1"]
        result = self.scraper._extract_text(soup, selectors)
        self.assertEqual(result, "Fallback Title")

    def test_extract_text_no_match(self):
        """Test text extraction with no matching selector."""
        html = """
        <html>
            <body>
                <div>No title here</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        selectors = ["h1.entry-title", "h1.post-title"]
        result = self.scraper._extract_text(soup, selectors)
        self.assertIsNone(result)


class TestDataClasses(unittest.TestCase):
    """Test data class initialization."""

    def test_rupiah_data_creation(self):
        """Test RupiahData creation."""
        data = RupiahData(
            title="Test Title",
            opening_rate=16000.0,
            current_rate=16100.0,
            time_wib="10:00",
            percentage_change=-0.5,
            trend="melemah",
            asian_currencies=[{"name": "Yen", "change_pct": 0.2}],
            content="Test content",
        )
        self.assertEqual(data.title, "Test Title")
        self.assertEqual(data.current_rate, 16100.0)

    def test_gold_data_creation(self):
        """Test GoldData creation."""
        data = GoldData(
            title="Gold Title",
            antam_price=1000000.0,
            antam_change=5000.0,
            antam_trend="naik",
            buyback_price=900000.0,
            buyback_change=4500.0,
            global_gold_usd=2000.0,
            global_gold_change_pct=0.5,
            date="21 February 2026",
            content="Test content",
        )
        self.assertEqual(data.title, "Gold Title")
        self.assertEqual(data.antam_trend, "naik")


if __name__ == "__main__":
    unittest.main()
