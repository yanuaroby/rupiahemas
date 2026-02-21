# Product Requirements Document (PRD): BloombergTechnoz Financial Script Bot

## 1. Objective
To build a Python-based automation tool that scrapes financial data (Gold and Rupiah) from BloombergTechnoz.com, summarizes the key information using an LLM, and formats it into structured, non-clickbait scripts for TikTok/Reels. The scripts are delivered daily via Telegram at 09:00 AM (Mon-Fri).

## 2. Target Source
- **Website:** `bloombergtechnoz.com`
- **Focus Areas:** - Rupiah exchange rate (vs USD) and Asian market trends.
    - Gold prices (Antam & Global Gold) pada hari itu. contoh hari jumat 20 februari 2026.
    - keyword "emas/ antam" and "rupiah"

## 3. Core Features
- **Web Scraper:** Extracting the latest articles related to Rupiah and Gold.
- **Content Summarizer:** Distilling complex financial news into 2-4 concise sentences per section.
- **Script Generator:** Formatting the data into specific templates (Indonesian language).
- **Scheduler:** Automated execution at 09:00 AM WIB, Monday to Friday.
- **Telegram Integration:** Sending the final scripts to a specific Telegram Bot/Channel.

## 4. Technical Stack
- **Language:** Python 3.x
- **Scraping:** BeautifulSoup4 or Scrapy, and `requests`.
- **LLM Integration:** Groq
- **Scheduler:** `APScheduler` (if running on a server) or **GitHub Actions** (for a 100% free serverless solution).
- **Communication:** `python-telegram-bot` or direct Telegram API requests.

## 5. Script Specifications & Logic

### A. Rupiah Script Logic
1.  **Title:** Derived from the website.
2.  **Intro:** Exactly 3 sentences (Day, Time, Value).
3.  **Opening Data:** Opening value + Percentage change.
4.  **Analysis 1:** 2-4 sentences on external/macro factors (e.g., Dollar Index).
5.  **Asian FX Table:** List Asian currencies (Peso, Yen, Ringgit, Yuan, Won, Baht) with % change if available.
6.  **Analysis 2:** 2-4 sentences on global/geopolitical or domestic factors (e.g., Interest rates).
7.  **Forecast:** Predicted range (e.g., Rp16.900 - Rp17.000).

### B. Gold Script Logic
1.  **Title:** Derived from the website.
2.  **Intro:** 1 sentence stating if the price is up/down.
3.  **Antam Price:** Current price, change value, and Buyback price (current + change).
4.  **Analysis 1:** 2 sentences linking Antam to Global Gold trends.
5.  **Global Gold:** Value in USD, conversion to IDR, and % change.
6.  **Analysis 2:** 2 sentences on catalysts (e.g., Geopolitics, Safe Haven).
7.  **Forecast:** Price range in USD and IDR.

## 6. Constraints
- **Tone:** Professional, structured, no clickbait.
- **Language:** Output scripts must be in **Indonesian**.
- **Cost:** Must utilize free-tier services (GitHub Actions for hosting, Free API tiers).
