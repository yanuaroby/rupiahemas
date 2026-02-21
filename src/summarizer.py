"""
Summarizer module using Groq LLM API.
Generates analysis and forecasts for financial scripts.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass

from groq import Groq

from .config import GROQ_API_KEY, GROQ_MODEL
from .scraper import RupiahData, GoldData


@dataclass
class RupiahAnalysis:
    """Analysis results for Rupiah script."""

    external_analysis: str  # 2-4 sentences on external/macro factors
    asian_currencies_text: str  # Formatted Asian currencies list
    global_domestic_analysis: str  # 2-4 sentences on global/domestic factors
    forecast_range: str  # Predicted price range


@dataclass
class GoldAnalysis:
    """Analysis results for Gold script."""

    global_correlation: str  # 2 sentences linking Antam to global gold
    forecast_range_usd: str  # Predicted range in USD
    forecast_range_idr: str  # Predicted range in IDR
    price_catalysts: str  # 2 sentences on price movement reasons


class GroqSummarizer:
    """Summarizer using Groq LLM API for financial analysis."""

    def __init__(self):
        if GROQ_API_KEY:
            self.client = Groq(api_key=GROQ_API_KEY)
        else:
            self.client = None

    def _generate_with_groq(self, prompt: str) -> Optional[str]:
        """Generate text using Groq API."""
        if not self.client:
            return None

        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Anda adalah analis keuangan profesional yang bertugas membuat ringkasan berita finansial dalam bahasa Indonesia yang formal dan terstruktur.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq API error: {e}")
            return None

    def _generate_fallback_analysis(
        self, data: RupiahData
    ) -> RupiahAnalysis:
        """Generate fallback analysis without LLM."""
        # External analysis based on data
        trend_word = "penguatan" if data.trend == "menguat" else "pelemahan"
        external_analysis = (
            f"Pergerakan {trend_word} rupiah dipengaruhi oleh dinamika pasar global. "
            f"Indeks dolar AS menunjukkan volatilitas yang berdampak pada mata uang emerging market. "
            f"Para investor terus memantau kebijakan bank sentral AS The Fed terkait suku bunga."
        )

        # Format Asian currencies
        if data.asian_currencies:
            currencies_text = ", ".join(
                [f"{c['name']} ({c['change_pct']:+.2f}%)" for c in data.asian_currencies]
            )
        else:
            currencies_text = "Data mata uang Asia tidak tersedia"

        # Global/domestic analysis
        global_domestic = (
            "Faktor domestik juga berperan dalam pergerakan rupiah hari ini. "
            "Kondisi ekonomi dalam negeri dan arus modal asing mempengaruhi sentimen pasar. "
            "Bank Indonesia diperkirakan akan terus menjaga stabilitas nilai tukar."
        )

        # Forecast based on current rate
        if data.current_rate:
            base = data.current_rate
            low = int(base - 50)
            high = int(base + 50)
            forecast = f"Rp {low:,} - Rp {high:,}/US$"
        else:
            forecast = "Rp 16.900 - Rp 17.000/US$"

        return RupiahAnalysis(
            external_analysis=external_analysis,
            asian_currencies_text=currencies_text,
            global_domestic_analysis=global_domestic,
            forecast_range=forecast,
        )

    def _generate_gold_fallback_analysis(
        self, data: GoldData, rupiah_rate: Optional[float]
    ) -> GoldAnalysis:
        """Generate fallback gold analysis without LLM."""
        # Global correlation
        trend_word = "kenaikan" if data.antam_trend == "naik" else "penurunan"
        global_corr = (
            f"Harga emas Antam mengikuti pergerakan harga emas dunia yang mengalami {trend_word}. "
            f"Korelasi antara harga domestik dan global tetap kuat seiring dengan fluktuasi nilai tukar rupiah."
        )

        # Forecast ranges
        if data.global_gold_usd:
            base_usd = data.global_gold_usd
            low_usd = int(base_usd - 20)
            high_usd = int(base_usd + 20)
            forecast_usd = f"US$ {low_usd} - US$ {high_usd}/troy ons"

            if rupiah_rate:
                conversion_rate = rupiah_rate / 31.1035  # grams to troy ons
                low_idr = int(low_usd * conversion_rate)
                high_idr = int(high_usd * conversion_rate)
                forecast_idr = f"Rp {low_idr:,} - Rp {high_idr:,}/gram"
            else:
                forecast_idr = "Rp 1.050.000 - Rp 1.100.000/gram"
        else:
            forecast_usd = "US$ 2.000 - US$ 2.050/troy ons"
            forecast_idr = "Rp 1.050.000 - Rp 1.100.000/gram"

        # Price catalysts
        catalysts = (
            "Faktor geopolitik global dan status safe haven emas mendorong pergerakan harga. "
            "Ekspektasi kebijakan moneter bank sentral utama juga mempengaruhi daya tarik logam mulia."
        )

        return GoldAnalysis(
            global_correlation=global_corr,
            forecast_range_usd=forecast_usd,
            forecast_range_idr=forecast_idr,
            price_catalysts=catalysts,
        )

    def analyze_rupiah(self, data: RupiahData) -> RupiahAnalysis:
        """Generate analysis for Rupiah data using LLM or fallback."""
        prompt = f"""
Berdasarkan data berikut, buat analisis finansial profesional dalam bahasa Indonesia:

JUDUL: {data.title}
TREND: {data.trend}
PERUBAHAN: {data.percentage_change}%
NILAI TUKAR PEMBUKAAN: {data.opening_rate}
NILAI TUKAR SAAT INI: {data.current_rate}
WAKTU: {data.time_wib} WIB
MATA UANG ASIA: {data.asian_currencies}

KONTEN BERITA:
{data.content[:1500]}

Tugas:
1. Buat 2-4 kalimat analisis faktor eksternal (indeks dolar, The Fed, pasar global)
2. Format daftar mata uang Asia dengan persentase
3. Buat 2-4 kalimat analisis faktor global/domestik
4. Berikan perkiraan range pelemahan/penguatan rupiah

Format output (gunakan pemisah |):
[Analisis Eksternal]|[Mata Uang Asia]|[Analisis Global/Domestik]|[Forecast Range]
"""

        response = self._generate_with_groq(prompt)

        if response and "|" in response:
            parts = response.split("|")
            if len(parts) >= 4:
                return RupiahAnalysis(
                    external_analysis=parts[0].strip(),
                    asian_currencies_text=parts[1].strip(),
                    global_domestic_analysis=parts[2].strip(),
                    forecast_range=parts[3].strip(),
                )

        # Use fallback if LLM fails
        return self._generate_fallback_analysis(data)

    def analyze_gold(
        self, data: GoldData, rupiah_rate: Optional[float] = None
    ) -> GoldAnalysis:
        """Generate analysis for Gold data using LLM or fallback."""
        prompt = f"""
Berdasarkan data berikut, buat analisis finansial profesional dalam bahasa Indonesia:

JUDUL: {data.title}
TREND: {data.antam_trend}
HARGA ANTAM: {data.antam_price}
PERUBAHAN ANTAM: {data.antam_change}
HARGA BUYBACK: {data.buyback_price}
HARGA EMAS DUNIA: {data.global_gold_usd} USD
PERUBAHAN EMAS DUNIA: {data.global_gold_change_pct}%
TANGGAL: {data.date}

KONTEN BERITA:
{data.content[:1500]}

Tugas:
1. Buat 2 kalimat korelasi emas Antam dengan emas dunia
2. Berikan perkiraan range kenaikan harga emas dunia dalam USD
3. Konversi forecast ke Rupiah (gunakan kurs {rupiah_rate} jika tersedia)
4. Buat 2 kalimat alasan kenaikan/penurunan harga

Format output (gunakan pemisah |):
[Korelasi Emas]|[Forecast USD]|[Forecast IDR]|[Alasan Kenaikan/Penurunan]
"""

        response = self._generate_with_groq(prompt)

        if response and "|" in response:
            parts = response.split("|")
            if len(parts) >= 4:
                return GoldAnalysis(
                    global_correlation=parts[0].strip(),
                    forecast_range_usd=parts[1].strip(),
                    forecast_range_idr=parts[2].strip(),
                    price_catalysts=parts[3].strip(),
                )

        # Use fallback if LLM fails
        return self._generate_gold_fallback_analysis(data, rupiah_rate)
