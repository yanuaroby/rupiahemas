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

    context_1: str  # Faktor eksternal (indeks dolar, The Fed)
    context_2: str  # Dampak ke mata uang Asia
    context_3: str  # Sentimen global (minyak, geopolitik)
    context_4: str  # Faktor domestik
    context_5: str  # Dampak/khawatiran pelaku pasar
    asian_currencies: list  # List of dicts: [{name, change_pct, trend}, ...]
    forecast_low: str  # Lower bound forecast
    forecast_high: str  # Upper bound forecast


@dataclass
class GoldAnalysis:
    """Analysis results for Gold script."""

    context_1: str  # Korelasi dengan emas dunia
    context_2: str  # Analisis perilaku investor/harga
    context_3: str  # Faktor eksternal (dolar, minyak)
    context_4: str  # Geopolitik & dampak energi
    context_5: str  # Harapan suku bunga & dolar AS
    forecast_usd_low: str  # USD forecast low
    forecast_usd_high: str  # USD forecast high
    forecast_idr_low: str  # IDR forecast low
    forecast_idr_high: str  # IDR forecast high


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

        # Forecast based on current rate
        if data.current_rate:
            base = data.current_rate
            low = int(base - 50)
            high = int(base + 50)
            forecast_low = f"{low:,}".replace(",", ".")
            forecast_high = f"{high:,}".replace(",", ".")
        else:
            forecast_low = "16.900"
            forecast_high = "17.000"

        return RupiahAnalysis(
            context_1="Pergerakan rupiah dipengaruhi oleh penguatan indeks dolar AS yang terjadi hari ini. The Fed diperkirakan akan mempertahankan suku bunga acuan pada level saat ini.",
            context_2=f"Penguatan dolar ini membuat mayoritas mata uang Asia melemah. {self._format_asian_currencies_context(data.asian_currencies)}",
            context_3="Sentimen pasar global yang tidak menentu akibat fluktuasi harga minyak mentah dunia menjadi tekanan tambahan bagi rupiah.",
            context_4="Dari sisi domestik, kondisi ekonomi dalam negeri masih menunjukkan resiliensi meski ada tekanan dari faktor eksternal.",
            context_5="Pelaku pasar khawatir dengan kondisi fiskal dan menunggu langkah Bank Indonesia dalam menjaga stabilitas nilai tukar.",
            asian_currencies=data.asian_currencies,
            forecast_low=forecast_low,
            forecast_high=forecast_high,
        )

    def _format_asian_currencies_context(self, asian_currencies: list) -> str:
        """Format Asian currencies for context text."""
        if not asian_currencies:
            return "Data mata uang Asia tidak tersedia."
        
        # Find weakest currency
        weakest = min(asian_currencies, key=lambda x: x.get('change_pct', 0))
        weakest_name = weakest.get('name', 'Mata uang')
        return f"{weakest_name} menjadi valuta Asia terlemah pagi ini."

    def _generate_gold_fallback_analysis(
        self, data: GoldData, rupiah_rate: Optional[float]
    ) -> GoldAnalysis:
        """Generate fallback gold analysis without LLM."""
        # Determine trend words
        trend_word = "Penurunan" if data.antam_trend == "turun" else "Kenaikan" if data.antam_trend == "naik" else "Pergerakan"
        
        # Forecast ranges
        if data.global_gold_usd:
            base_usd = data.global_gold_usd
            low_usd = int(base_usd - 20)
            high_usd = int(base_usd + 20)
            forecast_usd_low = f"{low_usd}"
            forecast_usd_high = f"{high_usd}"

            if rupiah_rate:
                conversion_rate = rupiah_rate / 31.1035  # grams to troy ons
                low_idr = int(low_usd * conversion_rate)
                high_idr = int(high_usd * conversion_rate)
                forecast_idr_low = f"{low_idr:,}".replace(",", ".")
                forecast_idr_high = f"{high_idr:,}".replace(",", ".")
            else:
                forecast_idr_low = "1.050.000"
                forecast_idr_high = "1.100.000"
        else:
            forecast_usd_low = "2.000"
            forecast_usd_high = "2.050"
            forecast_idr_low = "1.050.000"
            forecast_idr_high = "1.100.000"

        return GoldAnalysis(
            context_1=f"{trend_word.lower()} harga emas Antam hari ini sejalan dengan pergerakan harga emas dunia yang mengalami perubahan signifikan.",
            context_2=f"Pergerakan ini membuat investor kembali mempertimbangkan posisi mereka di pasar logam mulia.",
            context_3="Faktor eksternal termasuk fluktuasi indeks dolar AS dan harga minyak dunia mempengaruhi sentimen pasar emas.",
            context_4="Ketegangan geopolitik di berbagai wilayah berpotensi mendorong harga energi dan mendukung status safe haven emas.",
            context_5="Ekspektasi kebijakan suku bunga bank sentral utama tetap menjadi katalis utama bagi pergerakan harga emas ke depan.",
            forecast_usd_low=forecast_usd_low,
            forecast_usd_high=forecast_usd_high,
            forecast_idr_low=forecast_idr_low,
            forecast_idr_high=forecast_idr_high,
        )

    def analyze_rupiah(self, data: RupiahData) -> RupiahAnalysis:
        """Generate analysis for Rupiah data using LLM or fallback."""
        prompt = f"""
Berdasarkan data berikut, buat analisis finansial profesional dalam bahasa Indonesia untuk script TikTok/Reels:

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
1. Buat 5 kalimat analisis terpisah dengan struktur:
   - Konteks 1: Faktor eksternal (indeks dolar AS, The Fed, pasar global)
   - Konteks 2: Dampak ke mata uang Asia (sebutkan yang terlemah)
   - Konteks 3: Sentimen global (minyak mentah, geopolitik)
   - Konteks 4: Faktor domestik (ekonomi dalam negeri, kebijakan pemerintah)
   - Konteks 5: Dampak/khawatiran pelaku pasar

2. Extract semua mata uang Asia yang ada di artikel dengan format: nama, persentase, trend (melemah/menguat)

3. Berikan perkiraan range pelemahan/penguatan rupiah (low dan high)

Format output (gunakan pemisah |):
[Konteks 1]|[Konteks 2]|[Konteks 3]|[Konteks 4]|[Konteks 5]|[Mata Uang Asia JSON]|[Forecast Low]|[Forecast High]

Contoh Mata Uang Asia JSON:
[{{"name": "Peso Filipina", "change_pct": -0.5, "trend": "melemah"}}, {{"name": "Yen Jepang", "change_pct": -0.3, "trend": "melemah"}}]
"""

        response = self._generate_with_groq(prompt)

        if response and "|" in response:
            parts = response.split("|")
            if len(parts) >= 8:
                import json
                try:
                    asian_currencies = json.loads(parts[5].strip())
                except (json.JSONDecodeError, ValueError):
                    asian_currencies = data.asian_currencies
                
                return RupiahAnalysis(
                    context_1=parts[0].strip(),
                    context_2=parts[1].strip(),
                    context_3=parts[2].strip(),
                    context_4=parts[3].strip(),
                    context_5=parts[4].strip(),
                    asian_currencies=asian_currencies,
                    forecast_low=parts[6].strip(),
                    forecast_high=parts[7].strip(),
                )

        # Use fallback if LLM fails
        return self._generate_fallback_analysis(data)

    def analyze_gold(
        self, data: GoldData, rupiah_rate: Optional[float] = None
    ) -> GoldAnalysis:
        """Generate analysis for Gold data using LLM or fallback."""
        prompt = f"""
Berdasarkan data berikut, buat analisis finansial profesional dalam bahasa Indonesia untuk script TikTok/Reels:

JUDUL: {data.title}
TREND: {data.antam_trend}
HARGA ANTAM: {data.antam_price}
PERUBAHAN ANTAM: {data.antam_change}
HARGA BUYBACK: {data.buyback_price}
HARGA EMAS DUNIA: {data.global_gold_usd} USD
PERUBAHAN EMAS DUNIA: {data.global_gold_change_pct}%
TANGGAL: {data.date}
KURS RUPIAH: {rupiah_rate}

KONTEN BERITA:
{data.content[:1500]}

Tugas:
1. Buat 5 kalimat analisis terpisah dengan struktur:
   - Konteks 1: Korelasi harga emas Antam dengan emas dunia (sebutkan persentase perubahan)
   - Konteks 2: Analisis perilaku investor/harga (apakah investor memburu emas karena harga terjangkau)
   - Konteks 3: Faktor eksternal (indeks dolar AS, harga minyak dunia)
   - Konteks 4: Geopolitik & dampak energi (perang, risiko harga energi)
   - Konteks 5: Harapan suku bunga & dampak ke dolar AS

2. Berikan perkiraan range harga emas dunia dalam USD (low dan high)

3. Konversi forecast ke Rupiah (gunakan kurs {rupiah_rate if rupiah_rate else 16000})

Format output (gunakan pemisah |):
[Konteks 1]|[Konteks 2]|[Konteks 3]|[Konteks 4]|[Konteks 5]|[Forecast USD Low]|[Forecast USD High]|[Forecast IDR Low]|[Forecast IDR High]
"""

        response = self._generate_with_groq(prompt)

        if response and "|" in response:
            parts = response.split("|")
            if len(parts) >= 9:
                return GoldAnalysis(
                    context_1=parts[0].strip(),
                    context_2=parts[1].strip(),
                    context_3=parts[2].strip(),
                    context_4=parts[3].strip(),
                    context_5=parts[4].strip(),
                    forecast_usd_low=parts[5].strip(),
                    forecast_usd_high=parts[6].strip(),
                    forecast_idr_low=parts[7].strip(),
                    forecast_idr_high=parts[8].strip(),
                )

        # Use fallback if LLM fails
        return self._generate_gold_fallback_analysis(data, rupiah_rate)
