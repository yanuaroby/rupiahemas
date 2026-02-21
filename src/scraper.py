"""
Web scraper module for BloombergTechnoz.com.
Extracts Rupiah and Gold (Antam) financial data.
"""

import re
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from .config import BASE_URL, HEADERS, REQUEST_TIMEOUT, RUPIAH_KEYWORD, GOLD_KEYWORD


@dataclass
class RupiahData:
    """Data class for Rupiah exchange rate information."""

    title: str
    opening_rate: Optional[float]
    current_rate: Optional[float]
    time_wib: Optional[str]
    percentage_change: Optional[float]
    trend: Optional[str]  # "melemah" or "menguat"
    asian_currencies: List[Dict[str, Any]]
    content: str


@dataclass
class GoldData:
    """Data class for Gold price information."""

    title: str
    antam_price: Optional[float]
    antam_change: Optional[float]
    antam_trend: Optional[str]  # "naik", "turun", or "stagnan"
    buyback_price: Optional[float]
    buyback_change: Optional[float]
    global_gold_usd: Optional[float]
    global_gold_change_pct: Optional[float]
    date: Optional[str]
    content: str


class BloombergTechnozScraper:
    """Scraper for BloombergTechnoz.com financial data."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page."""
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _search_articles(self, keyword: str) -> List[str]:
        """Search for articles by keyword and return URLs."""
        search_url = f"{BASE_URL}/?s={keyword}"
        soup = self._fetch_page(search_url)
        if not soup:
            return []

        urls = []
        # Multiple selector fallbacks for search results
        selectors = [
            "article h2 a",
            "article h3 a",
            ".entry-title a",
            ".post-title a",
            "h2 a[href]",
            ".wp-block-post-title a",
        ]

        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                href = elem.get("href")
                if href and href not in urls:
                    urls.append(href)
            if urls:
                break

        return urls[:3]  # Return top 3 results

    def _extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract text using multiple selector fallbacks."""
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return None

    def _extract_number(self, text: Optional[str]) -> Optional[float]:
        """Extract numeric value from text (handles Indonesian format)."""
        if not text:
            return None
        # Remove "Rp", ".", and other non-numeric chars except decimal
        cleaned = re.sub(r"[^\d,.-]", "", text.replace(".", "").replace(",", "."))
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _extract_percentage(self, text: Optional[str]) -> Optional[float]:
        """Extract percentage value from text."""
        if not text:
            return None
        match = re.search(r"([+-]?\d+\.?\d*)\s*%", text)
        if match:
            return float(match.group(1))
        return None

    def _determine_trend(self, percentage: Optional[float]) -> Optional[str]:
        """Determine trend based on percentage change."""
        if percentage is None:
            return None
        if percentage > 0:
            return "menguat"
        elif percentage < 0:
            return "melemah"
        return "stagnan"

    def _determine_gold_trend(self, change: Optional[float]) -> Optional[str]:
        """Determine gold trend based on price change."""
        if change is None:
            return None
        if change > 0:
            return "naik"
        elif change < 0:
            return "turun"
        return "stagnan"

    def _extract_article_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content."""
        # Multiple selector fallbacks for article content
        selectors = [
            ".entry-content",
            ".post-content",
            "article .content",
            ".wp-block-post-content",
            ".entry-content p",
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                # Get all paragraph text
                paragraphs = elem.find_all("p") if "p" not in selector else [elem]
                content = " ".join([p.get_text(strip=True) for p in paragraphs])
                return content

        # Fallback: get all text from body
        body = soup.find("body")
        if body:
            return body.get_text(strip=True)[:2000]

        return ""

    def _parse_rupiah_from_content(self, content: str) -> Dict[str, Any]:
        """Parse Rupiah data from article content."""
        data = {
            "opening_rate": None,
            "current_rate": None,
            "time_wib": None,
            "percentage_change": None,
            "asian_currencies": [],
        }

        # Extract opening rate (pembukaan)
        opening_patterns = [
            r"level\s+([\d\.]+)\s*/\s*US\$",
            r"pembukaan[^/]+?([\d\.]+)\s*/\s*US\$",
            r"[Pp]ada\s+pembukaan[^/]+?([\d\.]+)",
            r"dibuka[^/]+?([\d\.]+)\s*/\s*US\$",
            r"Rp\s*([\d\.]+)\s*/\s*US\$\s+pada pembukaan",
            r"pada pembukaan[^/]+?Rp\s*([\d\.]+)",
        ]
        for pattern in opening_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # Get the last non-None group
                groups = [g for g in match.groups() if g is not None]
                if groups:
                    data["opening_rate"] = float(groups[-1].replace(".", ""))
                break

        # Extract current rate
        current_patterns = [
            r"bergerak[\s\w]+?(\d+\.?\d*)\s*/\s*US\$",
            r"berada[\s\w]+?(\d+\.?\d*)\s*/\s*US\$",
            r"diperdagangkan[\s\w]+?(\d+\.?\d*)\s*/\s*US\$",
            r"rupiah dihargai\s*(\d+\.?\d*)\s*/\s*US\$",
        ]
        for pattern in current_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                data["current_rate"] = float(match.group(1).replace(".", ""))
                break

        # Extract time (WIB)
        time_patterns = [
            r"pukul\s*(\d{1,2}:\d{2})\s*WIB",
            r"(\d{1,2}:\d{2})\s*WIB",
            r"pada\s*(\d{1,2}:\d{2})",
        ]
        for pattern in time_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                data["time_wib"] = match.group(1)
                break

        # Extract percentage change
        # Order matters: check trend word patterns first
        pct_patterns = [
            r"(melemah|menguat)\s*(\d+\.?\d*)\s*%\s*(?:dari sebelumnya)?",
            r"([+-]?\d+\.?\d*)\s*%\s*(?:dari sebelumnya|terhadap.*sebelumnya)",
            r"([+-]?\d+\.?\d*)\s*%",
        ]
        for pattern in pct_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 2 and groups[0] in ["melemah", "menguat"]:
                        # Pattern with trend word
                        trend_word = groups[0].lower()
                        pct_value = float(groups[1])
                        if trend_word == "melemah":
                            pct_value = -pct_value
                        data["percentage_change"] = pct_value
                    else:
                        # Pattern with sign
                        pct_value = float(groups[0].replace("-", ""))
                        if "-" in match.group(1) or "melemah" in match.group(0).lower():
                            pct_value = -pct_value
                        data["percentage_change"] = pct_value
                except (ValueError, IndexError):
                    pass
                break

        # Extract Asian currencies
        asian_currencies = []
        currency_names = {
            "peso": "Peso",
            "yen": "Yen",
            "ringgit": "Ringgit",
            "yuan": "Yuan",
            "won": "Won",
            "baht": "Baht",
            "dolar singapura": "Dolar Singapura",
            "dolar hong kong": "Dolar Hong Kong",
        }

        for currency, name in currency_names.items():
            pattern = rf"{currency}[\s\w]+?([+-]?\d+\.?\d*)\s*%"
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    pct = float(match.group(1))
                    asian_currencies.append({"name": name, "change_pct": pct})
                except ValueError:
                    pass

        data["asian_currencies"] = asian_currencies

        return data

    def _parse_gold_from_content(self, content: str) -> Dict[str, Any]:
        """Parse Gold data from article content."""
        data = {
            "antam_price": None,
            "antam_change": None,
            "buyback_price": None,
            "buyback_change": None,
            "global_gold_usd": None,
            "global_gold_change_pct": None,
            "date": None,
        }

        # Extract Antam price
        antam_patterns = [
            r"Rp\s*([\d\.]+)\s*/\s*gram",
            r"Antam[\s\w]+?Rp\s*([\d\.]+)",
            r"harga emas[\s\w]+?Rp\s*([\d\.]+)",
        ]
        for pattern in antam_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # Remove all dots (Indonesian thousand separator)
                price_str = match.group(1).replace(".", "")
                data["antam_price"] = float(price_str)
                break

        # Extract Antam change
        change_patterns = [
            r"(naik|turun)\s*Rp\s*(\d+\.?\d*)\s*/\s*gram",
            r"(naik|turun)\s*Rp\s*(\d+\.?\d*)",
            r"([+-]\s*Rp\s*\d+\.?\d*)",
        ]
        for pattern in change_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 2:
                        trend = match.group(1).lower()
                        change_str = match.group(2).replace(".", "")
                        change = float(change_str)
                        if trend == "turun":
                            change *= -1
                        data["antam_change"] = change
                    else:
                        change_str = match.group(1).replace("Rp", "").replace(" ", "")
                        data["antam_change"] = float(change_str.replace(".", ""))
                except ValueError:
                    pass
                break

        # Extract buyback price
        buyback_patterns = [
            r"buyback[\s\w]+?Rp\s*(\d+\.?\d*)",
            r"harga buyback[\s\w]+?Rp\s*(\d+\.?\d*)",
            r"Rp\s*(\d+\.?\d*)\s*/\s*gram.*buyback",
        ]
        for pattern in buyback_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(".", "")
                data["buyback_price"] = float(price_str)
                break

        # Extract global gold price
        global_patterns = [
            r"emas dunia[\s\w]+?US\$\s*(\d+\.?\d*)",
            r"global[\s\w]+?US\$\s*(\d+\.?\d*)",
            r"spot[\s\w]+?US\$\s*(\d+\.?\d*)",
            r"XAU/USD[\s\w]+?(\d+\.?\d*)",
        ]
        for pattern in global_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                data["global_gold_usd"] = float(match.group(1).replace(",", ""))
                break

        # Extract global gold percentage change
        global_pct_patterns = [
            r"([+-]?\d+\.?\d*)\s*%\s*(?:dari hari sebelumnya|pada.*sebelumnya)",
            r"(bertambah|berkurang)\s*([+-]?\d+\.?\d*)\s*%",
        ]
        for pattern in global_pct_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    data["global_gold_change_pct"] = float(match.group(1))
                except ValueError:
                    pass
                break

        # Extract date
        date_patterns = [
            r"(\d{1,2}\s+\w+\s+\d{4})",
            r"(\d{1,2}/\d{1,2}/\d{4})",
            r"(\w+\s+\d{1,2},\s+\d{4})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                data["date"] = match.group(1)
                break

        return data

    def scrape_rupiah(self) -> Optional[RupiahData]:
        """Scrape latest Rupiah news and data."""
        urls = self._search_articles(RUPIAH_KEYWORD)

        for url in urls:
            soup = self._fetch_page(url)
            if not soup:
                continue

            # Extract title
            title_selectors = [
                "h1.entry-title",
                "h1.post-title",
                "h1.wp-block-post-title",
                "article h1",
                "h1",
            ]
            title = self._extract_text(soup, title_selectors)
            if not title:
                continue

            # Extract content
            content = self._extract_article_content(soup)
            if not content:
                continue

            # Parse rupiah data from content
            parsed = self._parse_rupiah_from_content(content)

            return RupiahData(
                title=title,
                opening_rate=parsed["opening_rate"],
                current_rate=parsed["current_rate"],
                time_wib=parsed["time_wib"],
                percentage_change=parsed["percentage_change"],
                trend=self._determine_trend(parsed["percentage_change"]),
                asian_currencies=parsed["asian_currencies"],
                content=content,
            )

        return None

    def scrape_gold(self) -> Optional[GoldData]:
        """Scrape latest Gold (Antam) news and data."""
        urls = self._search_articles(GOLD_KEYWORD)

        for url in urls:
            soup = self._fetch_page(url)
            if not soup:
                continue

            # Extract title
            title_selectors = [
                "h1.entry-title",
                "h1.post-title",
                "h1.wp-block-post-title",
                "article h1",
                "h1",
            ]
            title = self._extract_text(soup, title_selectors)
            if not title:
                continue

            # Extract content
            content = self._extract_article_content(soup)
            if not content:
                continue

            # Parse gold data from content
            parsed = self._parse_gold_from_content(content)

            # Get current date if not found
            date = parsed["date"]
            if not date:
                date = datetime.now().strftime("%d %B %Y")

            return GoldData(
                title=title,
                antam_price=parsed["antam_price"],
                antam_change=parsed["antam_change"],
                antam_trend=self._determine_gold_trend(parsed["antam_change"]),
                buyback_price=parsed["buyback_price"],
                buyback_change=parsed["buyback_change"],
                global_gold_usd=parsed["global_gold_usd"],
                global_gold_change_pct=parsed["global_gold_change_pct"],
                date=date,
                content=content,
            )

        return None
