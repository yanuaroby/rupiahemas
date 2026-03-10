"""
Web scraper module for BloombergTechnoz.com.
Extracts Rupiah and Gold (Antam) financial data.
"""

import re
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

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
        # Use httpx Client with HTTP/2 support and connection pooling
        self.client = httpx.Client(http2=True, headers=HEADERS, timeout=REQUEST_TIMEOUT)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page with automatic retry."""
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except httpx.HTTPError as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _search_articles(self, keyword: str, max_days_back: int = 5, prefer_weekday: bool = True) -> List[str]:
        """Search for articles by keyword using sitemap, preferring weekday articles."""
        from datetime import datetime, timedelta

        urls = []

        # Primary method: Use news sitemap
        try:
            sitemap_url = f"{BASE_URL}/sitemap-news.xml"
            soup = self._fetch_page(sitemap_url)
            if soup:
                locs = soup.find_all('loc')
                
                # Collect articles with their dates
                weekday_articles = []
                weekend_articles = []
                
                for loc in locs:
                    url_text = loc.text
                    # Filter by keyword
                    if keyword.lower() in url_text.lower():
                        # Fetch article to get publish date
                        article_soup = self._fetch_page(url_text)
                        if article_soup:
                            # Extract date from article
                            date_str = self._extract_article_date(article_soup)
                            if date_str:
                                try:
                                    # Parse date (format: 20 February 2026)
                                    article_date = datetime.strptime(date_str, "%d %B %Y")
                                    is_weekday = article_date.weekday() < 5
                                    
                                    if is_weekday:
                                        weekday_articles.append((url_text, article_date))
                                    else:
                                        weekend_articles.append((url_text, article_date))
                                except ValueError:
                                    weekday_articles.append((url_text, None))
                
                # Prefer weekday articles
                if prefer_weekday and weekday_articles:
                    # Sort by date (most recent first)
                    weekday_articles.sort(key=lambda x: x[1] if x[1] else datetime.now(), reverse=True)
                    print(f"  Found {len(weekday_articles)} weekday articles from sitemap for '{keyword}'")
                    return [url for url, _ in weekday_articles[:5]]
                
                # Fallback to weekend articles
                if weekend_articles:
                    weekend_articles.sort(key=lambda x: x[1] if x[1] else datetime.now(), reverse=True)
                    print(f"  Found {len(weekend_articles)} weekend articles from sitemap for '{keyword}'")
                    return [url for url, _ in weekend_articles[:5]]
                    
        except Exception as e:
            print(f"  Sitemap search error: {e}")

        # Fallback: Try search URLs
        search_urls = [
            f"{BASE_URL}/?s={keyword}",
            f"{BASE_URL}/page/1/?s={keyword}",
        ]

        for search_url in search_urls:
            soup = self._fetch_page(search_url)
            if not soup:
                continue

            selectors = [
                "article h2 a",
                ".entry-title a",
                "h2 a[href]",
                "a[href*='/202']",
                "a[href*='/detail']",
            ]

            for selector in selectors:
                elements = soup.select(selector)
                for elem in elements:
                    href = elem.get("href")
                    text = elem.get_text(strip=True)
                    if href and text and keyword.lower() in text.lower():
                        if href not in urls:
                            urls.append(href)
                if urls:
                    break

            if urls:
                break

        # Second fallback: Homepage
        if not urls:
            print(f"  Trying homepage fallback...")
            homepage = self._fetch_page(BASE_URL)
            if homepage:
                all_links = homepage.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href')
                    text = link.get_text(strip=True).lower()
                    if href and keyword.lower() in text:
                        if href not in urls:
                            urls.append(href)

        return urls[:5]

    def _extract_article_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publish date from article page."""
        # Try multiple selectors
        selectors = [
            "time",
            ".date",
            ".published",
            ".article-date",
            ".post-date",
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        # Try meta tag
        meta = soup.find("meta", property="article:published_time")
        if meta:
            return meta.get("content")
        
        # Try regex in content
        import re
        content = str(soup)
        match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})\s+\d{2}:\d{2}', content)
        if match:
            return match.group(1)
        
        return None

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
            ".article-content",
            ".news-content",
            ".detail-content",
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                # Get all paragraph text
                paragraphs = elem.find_all("p")
                if paragraphs:
                    content = " ".join([p.get_text(strip=True) for p in paragraphs])
                    return content
                else:
                    return elem.get_text(strip=True)

        # Fallback: get text from article tag
        article = soup.find("article")
        if article:
            return article.get_text(strip=True)[:2000]

        # Last fallback: get all text from body
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
            r"pembukaan[\s\w]+?di\s+level\s*([\d\.]+)\s*/\s*US\$",
            r"pembukaan[\s\w]+?([\d\.]+)\s*/\s*US\$",
            r"[Pp]ada\s+pembukaan[^/]+?([\d\.]+)",
            r"dibuka[^/]+?([\d\.]+)\s*/\s*US\$",
            r"Rp\s*([\d\.]+)\s*/\s*US\$\s+pada pembukaan",
            r"pada pembukaan[^/]+?Rp\s*([\d\.]+)",
            r"melemah[\s\w]+?Rp\s*([\d\.]+)\s*/\s*US\$",
            r"menguat[\s\w]+?Rp\s*([\d\.]+)\s*/\s*US\$",
        ]
        for pattern in opening_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # Get the last non-None group
                groups = [g for g in match.groups() if g is not None]
                if groups:
                    data["opening_rate"] = float(groups[-1].replace(".", ""))
                break

        # Extract current rate (penutupan or current)
        current_patterns = [
            r"ditutup[\s\w]+?Rp\s*([\d\.]+)\s*/US\$",
            r"penutupan[\s\w]+?Rp\s*([\d\.]+)\s*/US\$",
            r"bergerak[\s\w]+?(?:ke\s+angka|ke\s+posisi|di)\s*(?:Rp\s*)?([\d\.]+)\s*/US\$",
            r"berada[\s\w]+?Rp\s*([\d\.]+)\s*/US\$",
            r"diperdagangkan[\s\w]+?Rp\s*([\d\.]+)\s*/US\$",
            r"rupiah dihargai\s*Rp\s*([\d\.]+)\s*/US\$",
            r"menguat[\s\w]+?ke\s+posisi\s+Rp\s*([\d\.]+)\s*/US\$",
            r"melemah[\s\w]+?ke\s+posisi\s+Rp\s*([\d\.]+)\s*/US\$",
            r"di\s+posisi\s+Rp\s*([\d\.]+)\s*/US\$",
            r"Rp\s*([\d\.]+)\s*/US\$[\s\w]+,?\s+setelah",
            r"Rp\s*([\d\.]+)\s*/US\$\s+sore ini",
            r"ke\s+posisi\s+Rp\s*([\d\.]+)\s*/US\$",
            r"Rp([\d\.]+)/US",
        ]
        for pattern in current_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                groups = [g for g in match.groups() if g is not None]
                if groups:
                    data["current_rate"] = float(groups[-1].replace(".", ""))
                break

        # Extract time (WIB)
        time_patterns = [
            r"pukul\s*(\d{1,2}:\d{2})\s*WIB",
            r"(\d{1,2}:\d{2})\s*WIB",
            r"pada\s*(\d{1,2}:\d{2})",
            r"sore ini\s+\((\d{1,2}/\d{1,2}/\d{4})\)",
        ]
        for pattern in time_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                data["time_wib"] = match.group(1)
                break

        # Extract percentage change
        # Order matters: check trend word patterns first
        pct_patterns = [
            r"(melemah|menguat)\s*(\d+[,\.]?\d*)\s*%\s*(?:dari sebelumnya)?",
            r"([\d,]+)\s*%\s*(?:dari sebelumnya|terhadap.*sebelumnya)",
            r"([+-]?\d+[,\.]?\d*)\s*%",
            r"menguat\s+([\d,]+)\s*persen",
            r"melemah\s+([\d,]+)\s*persen",
        ]
        for pattern in pct_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) >= 2 and groups[0] in ["melemah", "menguat"]:
                        # Pattern with trend word
                        trend_word = groups[0].lower()
                        pct_str = groups[1].replace(",", ".")
                        pct_value = float(pct_str) if pct_str else 0
                        if trend_word == "melemah":
                            pct_value = -pct_value
                        data["percentage_change"] = pct_value
                    else:
                        # Pattern with sign or just number
                        pct_str = groups[0].replace(",", ".").replace("-", "")
                        pct_value = float(pct_str) if pct_str else 0
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
            "rupee": "Rupee",
        }

        for currency, name in currency_names.items():
            pattern = rf"{currency}[\s\w]+?([+-]?\d+\.?\d*)\s*%"
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    pct = float(match.group(1))
                    # Determine trend based on percentage sign
                    trend = "melemah" if pct < 0 else "menguat"
                    asian_currencies.append({"name": name, "change_pct": pct, "trend": trend})
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
            r"(naik|turun|menguat|melemah|bertambah|berkurang)\s*Rp\s*(\d+\.?\d*)\s*/\s*gram",
            r"(naik|turun|menguat|melemah|bertambah|berkurang)\s*Rp\s*(\d+\.?\d*)",
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
                        # Map trend words to direction
                        if trend in ["turun", "melemah", "berkurang"]:
                            change *= -1
                        data["antam_change"] = change
                    else:
                        change_str = match.group(1).replace("Rp", "").replace(" ", "")
                        data["antam_change"] = float(change_str.replace(".", ""))
                except ValueError:
                    pass
                break

        # Extract buyback price - try most specific patterns first
        buyback_patterns = [
            r"pembelian kembali.*?Rp\s*(\d[\d\.]*)\s*/\s*gram",  # Most specific: "pembelian kembali (buyback) ... Rp 2.802.000/gram"
            r"ada di Rp\s*(\d[\d\.]*)\s*/\s*gram",  # "ada di Rp 2.802.000/gram"
            r"buyback[\s\w]+?Rp\s*(\d[\d\.]*)\s*/\s*gram",  # "buyback ... Rp X/gram"
            r"harga buyback[\s\w]+?Rp\s*(\d[\d\.]*)\s*/\s*gram",  # "harga buyback ... Rp X/gram"
        ]
        for pattern in buyback_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # Remove ALL dots (Indonesian thousand separator)
                price_str = match.group(1).replace(".", "")
                # Need at least 4 digits for valid price (e.g., 2802000)
                if len(price_str) >= 4:
                    data["buyback_price"] = float(price_str)
                    break

        # Extract buyback change - look for it AFTER buyback price context
        buyback_change_patterns = [
            r"buyback[\s\w]+?bertambah\s*Rp\s*(\d+\.?\d*)",  # Specific to buyback
            r"buyback[\s\w]+?berkurang\s*Rp\s*(\d+\.?\d*)",
            r"pembelian kembali[\s\w]+?bertambah\s*Rp\s*(\d+\.?\d*)",
            r"pembelian kembali[\s\w]+?berkurang\s*Rp\s*(\d+\.?\d*)",
            r"bertambah\s*Rp\s*(\d+\.?\d*)\s*dibandingkan.*?sebelumnya",  # General "bertambah" with context
            r"berkurang\s*Rp\s*(\d+\.?\d*)\s*dibandingkan.*?sebelumnya",
        ]
        for pattern in buyback_change_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    change_str = match.group(1).replace(".", "")
                    change = float(change_str)
                    # Check if pattern contains "berkurang" for negative
                    if "berkurang" in pattern.lower():
                        change *= -1
                    data["buyback_change"] = change
                except ValueError:
                    pass
                break

        # Extract global gold price - prefer latest price (morning/today over closing)
        global_patterns = [
            # Priority 1: Most specific morning patterns with percentage context
            r"melemah\s+[\d,]+%\s+ke\s+([\d\.]+,\d+)\s*/troy",  # "melemah 0,11% ke 5.133,7/troy"
            r"menguat\s+[\d,]+%\s+ke\s+([\d\.]+,\d+)\s*/troy",  # "menguat X% ke Y/troy"
            # Priority 2: Morning/today price patterns (with DOTALL for multiline)
            r"pagi ini.*?Selasa.*?([\d\.]+,\d+)\s*/troy",  # "Pagi ini, Selasa ... 5.133,7/troy"
            r"masih melemah.*?([\d\.]+,\d+)\s*/troy",  # "masih melemah ... X/troy"
            r"masih menguat.*?([\d\.]+,\d+)\s*/troy",  # "masih menguat ... X/troy"
            r"pada pukul\s+\d{1,2}:\d{2}.*?([\d\.]+,\d+)\s*/troy",  # Price with timestamp
            # Priority 3: General patterns (closing price)
            r"([\d\.]+,\d+)\s*/troy\s*ons",  # European format: 5.129,5/troy ons
            r"US.*?([\d\.]+,\d+)\s*/troy",  # With US prefix
            r"US.*?([\d\.]+)",       # US with number
            r"di\s+([\d\.]+,\d+)",      # European format without /troy
            r"emas dunia.*?([\d\.]+,\d+)",
            r"emas dunia.*?([\d\.]+)",
            r"global.*?([\d\.]+,\d+)",
            r"global.*?([\d\.]+)",
            r"spot.*?([\d\.]+,\d+)",
            r"spot.*?([\d\.]+)",
            r"XAU/USD.*?([\d\.]+,\d+)",
            r"XAU/USD.*?([\d\.]+)",
        ]
        for pattern in global_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                raw_value = match.group(1)
                # Convert European format (4.997,7) to US format (4997.7)
                # Remove dots (thousand separator), replace comma with dot (decimal)
                normalized = raw_value.replace(".", "").replace(",", ".")
                data["global_gold_usd"] = float(normalized)
                break

        # Extract global gold percentage change - prefer most recent (morning/today)
        global_pct_patterns = [
            # Priority 1: Morning/today percentage patterns (with DOTALL for multiline)
            r"pagi ini.*?melemah\s+([\d,]+)\s*%",  # pagi ini ... melemah 0,11%
            r"pagi ini.*?menguat\s+([\d,]+)\s*%",   # pagi ini ... menguat X%
            r"masih melemah\s+([\d,]+)\s*%",  # masih melemah 0,11%
            r"masih menguat\s+([\d,]+)\s*%",  # masih menguat X%
            # Priority 2: Percentage with ke US$ pattern (indicates current price)
            r"melemah\s+([\d,]+)%\s+ke\s+US",  # melemah 0,11% ke US$
            r"menguat\s+([\d,]+)%\s+ke\s+US",  # menguat X% ke US$
            # Priority 3: General trend word patterns
            r"(terpangkas|melemah|turun)\s+([\d,]+)\s*%",  # Terpangkas 0,38% / Melemah 0,11%
            r"(bertambah|menguat|naik)\s+([\d,]+)\s*%",     # Bertambah 0,43% / Menguat 0,5%
            # Existing patterns with +/- signs
            r"([+-]?\d+,\d+)\s*%",                           # European decimal: +0,43%
            r"([\d,]+)\s*%\s*(?:dari hari sebelumnya)",      # 0,43% dari hari sebelumnya
            r"([+-]?\d+\.?\d*)\s*%\s*(?:dari hari sebelumnya|pada.*sebelumnya)",
        ]
        for pattern in global_pct_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) >= 2 and groups[0]:
                        # Pattern with trend word
                        trend_word = groups[0].lower()
                        pct_str = groups[1].replace(",", ".")
                        pct_value = float(pct_str)
                        # Determine sign based on trend word
                        if trend_word in ["terpangkas", "melemah", "turun", "berkurang"]:
                            pct_value = -pct_value
                        data["global_gold_change_pct"] = pct_value
                    elif len(groups) == 1:
                        # Pattern without trend word (just percentage)
                        raw_value = groups[0]
                        normalized = raw_value.replace(",", ".")
                        pct_value = float(normalized)
                        # Check if pattern contains negative indicators
                        if "turun" in match.group(0).lower() or "terpangkas" in match.group(0).lower() or "melemah" in match.group(0).lower():
                            pct_value = -abs(pct_value)
                        data["global_gold_change_pct"] = pct_value
                    else:
                        # Pattern with just number or +/- sign
                        raw_value = match.group(1)
                        normalized = raw_value.replace(",", ".")
                        pct_value = float(normalized)
                        # Check if pattern contains negative indicators
                        if "turun" in match.group(0).lower() or "terpangkas" in match.group(0).lower():
                            pct_value = -abs(pct_value)
                        data["global_gold_change_pct"] = pct_value
                except (ValueError, IndexError):
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

    def _search_global_gold_articles(self, max_results: int = 3) -> List[str]:
        """Search for global gold price articles."""
        # Try multiple keywords
        keywords = ["emas dunia", "harga emas turun", "harga emas naik", "gold"]
        
        for keyword in keywords:
            urls = self._search_articles(keyword, prefer_weekday=True)
            if urls:
                # Return top results
                return urls[:max_results]
        
        return []

    def _merge_global_gold_data(self, gold_data: GoldData) -> GoldData:
        """
        If GoldData doesn't have global gold price, search for it from
        a separate global gold article published on the same day.
        """
        # Check if we already have global gold data
        if gold_data.global_gold_usd and gold_data.global_gold_change_pct:
            return gold_data
        
        print("  No global gold data in Antam article, searching for global gold article...")
        
        # Search for global gold articles
        global_urls = self._search_global_gold_articles()
        
        for url in global_urls:
            soup = self._fetch_page(url)
            if not soup:
                continue
            
            # Extract content
            content = self._extract_article_content(soup)
            if not content:
                continue
            
            # Parse global gold data from content
            parsed = self._parse_gold_from_content(content)
            
            # Check if we found global gold data
            if parsed["global_gold_usd"] and parsed["global_gold_change_pct"]:
                print(f"  ✓ Found global gold data: US$ {parsed['global_gold_usd']}, {parsed['global_gold_change_pct']}%")
                # Merge data
                return GoldData(
                    title=gold_data.title,
                    antam_price=gold_data.antam_price,
                    antam_change=gold_data.antam_change,
                    antam_trend=gold_data.antam_trend,
                    buyback_price=gold_data.buyback_price,
                    buyback_change=gold_data.buyback_change,
                    global_gold_usd=parsed["global_gold_usd"],
                    global_gold_change_pct=parsed["global_gold_change_pct"],
                    date=gold_data.date,
                    content=gold_data.content + " " + content[:500],  # Append global gold content
                )
        
        print("  ✗ No global gold data found in related articles")
        return gold_data

    def scrape_gold(self) -> Optional[GoldData]:
        """Scrape latest Gold (Antam) news and data."""
        # Search specifically for "antam" articles
        keyword = GOLD_KEYWORD

        # Search with weekday preference first
        urls = self._search_articles(keyword, prefer_weekday=True)

        # If no weekday articles found, try without preference
        if not urls:
            urls = self._search_articles(keyword, prefer_weekday=False)

        # Filter to ensure only articles with "antam" in the title are selected
        filtered_urls = []
        for url in urls:
            soup = self._fetch_page(url)
            if soup:
                title_selectors = [
                    "h1.entry-title",
                    "h1.post-title",
                    "h1.wp-block-post-title",
                    "article h1",
                    "h1",
                ]
                title = self._extract_text(soup, title_selectors)
                if title and "antam" in title.lower():
                    filtered_urls.append(url)
                    print(f"  ✓ Found Antam article: {title[:50]}...")
        
        urls = filtered_urls if filtered_urls else urls

        # Fallback: Direct URL to recent Antam article (if sitemap doesn't have it)
        if not urls:
            print(f"  Sitemap search failed, trying direct URL fallback...")
            direct_urls = [
                "https://www.bloombergtechnoz.com/detail-news/100188/naik-berikut-daftar-lengkap-harga-emas-antam-hari-ini",
            ]
            for url in direct_urls:
                soup = self._fetch_page(url)
                if soup:
                    # Check if article contains "antam"
                    content = self._extract_article_content(soup)
                    if content and "antam" in content.lower():
                        urls.append(url)
                        break

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

            # Only return if we found relevant Antam/gold data
            if parsed["antam_price"] or parsed["antam_change"] or "antam" in content.lower():
                # Get current date if not found
                date = parsed["date"]
                if not date:
                    # Extract from article
                    article_date = self._extract_article_date(soup)
                    date = article_date if article_date else datetime.now().strftime("%d %B %Y")

                gold_data = GoldData(
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
                
                # If no global gold data, try to merge from another article
                if not gold_data.global_gold_usd or not gold_data.global_gold_change_pct:
                    gold_data = self._merge_global_gold_data(gold_data)
                
                return gold_data

        return None
