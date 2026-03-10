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
