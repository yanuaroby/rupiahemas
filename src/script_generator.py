"""
Script generator module for formatting financial scripts.
Generates Rupiah and Gold scripts following the specified templates.
"""

from datetime import datetime
from typing import Optional

import pytz

from .scraper import RupiahData, GoldData
from .summarizer import RupiahAnalysis, GoldAnalysis
from .config import WIB_TIMEZONE


class ScriptGenerator:
    """Generates formatted scripts for TikTok/Reels based on templates."""

    def __init__(self):
        self.wib_tz = WIB_TIMEZONE

    def _format_number(self, value: Optional[float], decimal_places: int = 0) -> str:
        """Format number with Indonesian thousand separator (dot) and decimal separator (comma)."""
        if value is None:
            return "-"

        if decimal_places > 0:
            # Format with comma as decimal separator, dot as thousand separator
            formatted = f"{value:,.{decimal_places}f}"
            # Swap: comma -> temporary, dot -> comma, temporary -> dot
            return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

        return f"{int(value):,}".replace(",", ".")

    def _get_current_day_date(self) -> tuple:
        """Get current day name and date in WIB timezone."""
        now = datetime.now(self.wib_tz)
        day_name = now.strftime("%A")
        date_str = now.strftime("%d %B %Y")

        # Indonesian day names
        day_map = {
            "Monday": "Senin",
            "Tuesday": "Selasa",
            "Wednesday": "Rabu",
            "Thursday": "Kamis",
            "Friday": "Jumat",
            "Saturday": "Sabtu",
            "Sunday": "Minggu",
        }

        return day_map.get(day_name, day_name), date_str

    def generate_rupiah_script(
        self, data: RupiahData, analysis: RupiahAnalysis
    ) -> str:
        """
        Generate Rupiah script following the template.

        Template:
        JUDUL : [JUDUL DARI WEBSITE] Nilai tukar rupiah melemah atau menguat dalam pembukaan perdagangan hari ini.
        [Hari], [Tanggal], rupiah dihargai [Nilai]/US$. Kemudian pada pukul [Waktu] WIB, rupiah bergerak ke angka [Nilai]/US$.
        NILAI TUKAR RUPIAH [Nilai]/US$ [Melemah/Menguat] [X]% dari sebelumnya

        [2-4 Kalimat Analisis Faktor Eksternal]
        NILAI TUKAR MATA UANG ASIA [List Mata Uang & Persentase]

        [2-4 Kalimat Analisis Global/Domestik]
        PERKIRAAN PELEMAHAN RUPIAH [Range Harga]
        """
        day_name, date_str = self._get_current_day_date()

        # Get values with fallbacks
        current_rate = data.current_rate or data.opening_rate or 16000
        opening_rate = data.opening_rate or current_rate
        time_wib = data.time_wib or "10:00"
        percentage = data.percentage_change or 0
        trend = data.trend or "melemah"

        # Format the script
        script = f"""JUDUL : {data.title}

Nilai tukar rupiah {trend} dalam pembukaan perdagangan hari ini. {day_name}, {date_str}, rupiah dihargai {self._format_number(opening_rate)}/US$. Kemudian pada pukul {time_wib} WIB, rupiah bergerak ke angka {self._format_number(current_rate)}/US$.

NILAI TUKAR RUPIAH {self._format_number(current_rate)}/US$ {trend.capitalize()} {abs(percentage):.2f}% dari sebelumnya

{analysis.external_analysis}

NILAI TUKAR MATA UANG ASIA {analysis.asian_currencies_text}

{analysis.global_domestic_analysis}

PERKIRAAN PELEMAHAN RUPIAH {analysis.forecast_range}"""

        return script.strip()

    def generate_gold_script(
        self, data: GoldData, analysis: GoldAnalysis, rupiah_rate: Optional[float] = None
    ) -> str:
        """
        Generate Gold script following the template.

        Template:
        JUDUL : [JUDUL DARI WEBSITE] Harga emas PT Aneka Tambang Tbk atau Antam [naik/turun/stagnan].
        HARGA EMAS ANTAM [Tanggal] Rp [Harga]/gram. [Naik/Turun] Rp [Nilai]/gram dari hari sebelumnya
        HARGA BUYBACK EMAS ANTAM Rp [Harga]/gram. [Naik/Turun] Rp [Nilai]/gram dari sebelumnya

        [2 Kalimat korelasi emas dunia]
        HARGA EMAS DUNIA US$ [Nilai]/troy ons. Rp. [Konversi] [Bertambah/Berkurang] [X]% dari hari sebelumnya

        [2 Kalimat alasan kenaikan/penurunan]
        PERKIRAAN KENAIKAN HARGA EMAS DUNIA US$ [Range] atau Rp. [Konversi] hingga US$ [Range] atau Rp. [Konversi]
        """
        # Get values with fallbacks
        antam_price = data.antam_price or 1_000_000
        antam_change = abs(data.antam_change) if data.antam_change else 0
        antam_trend = data.antam_trend or "stagnan"
        buyback_price = data.buyback_price or int(antam_price * 0.9)
        buyback_change = abs(data.buyback_change) if data.buyback_change else int(antam_change * 0.9)

        global_gold = data.global_gold_usd or 2000
        global_change_pct = data.global_gold_change_pct or 0

        # Calculate IDR conversion for global gold
        if rupiah_rate:
            # Convert USD/troy oz to IDR/gram
            # 1 troy oz = 31.1035 grams
            global_gold_idr = int(global_gold * rupiah_rate / 31.1035)
        else:
            global_gold_idr = int(global_gold * 16000 / 31.1035)

        # Determine trend words
        trend_action = "Naik" if antam_trend == "naik" else "Turun" if antam_trend == "turun" else "Stagnan"
        change_word = "bertambah" if global_change_pct >= 0 else "berkurang"

        # Format the script
        script = f"""JUDUL : {data.title}

Harga emas PT Aneka Tambang Tbk atau Antam {antam_trend}. HARGA EMAS ANTAM {data.date} Rp {self._format_number(antam_price)}/gram. {trend_action} Rp {self._format_number(antam_change)}/gram dari hari sebelumnya

HARGA BUYBACK EMAS ANTAM Rp {self._format_number(buyback_price)}/gram. {trend_action} Rp {self._format_number(buyback_change)}/gram dari sebelumnya

{analysis.global_correlation}

HARGA EMAS DUNIA US$ {self._format_number(global_gold)}/troy ons. Rp. {self._format_number(global_gold_idr)} {change_word.capitalize()} {abs(global_change_pct):.2f}% dari hari sebelumnya

{analysis.price_catalysts}

PERKIRAAN KENAIKAN HARGA EMAS DUNIA {analysis.forecast_range_usd} atau {analysis.forecast_range_idr} hingga {analysis.forecast_range_usd} atau {analysis.forecast_range_idr}"""

        return script.strip()

    def format_for_telegram(self, script: str, script_type: str) -> str:
        """Format script for Telegram message with HTML styling."""
        header = f"📊 <b>SCRIPT {script_type.upper()}</b> 📊\n\n"
        footer = "\n\n────────────────────\nℹ️ <i>Data dari BloombergTechnoz.com</i>"

        # Escape HTML special characters
        escaped_script = script.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Convert markdown-style formatting to HTML
        escaped_script = escaped_script.replace("**", "<b>").replace("__", "<i>")
        
        # Handle bold titles (JUDUL : ...)
        import re
        escaped_script = re.sub(r'JUDUL : (.+)', r'<b>JUDUL : \1</b>', escaped_script)
        
        # Handle section headers (ALL CAPS lines)
        lines = escaped_script.split('\n')
        formatted_lines = []
        for line in lines:
            if line.isupper() and len(line) > 3:
                formatted_lines.append(f"<b>{line}</b>")
            else:
                formatted_lines.append(line)
        escaped_script = '\n'.join(formatted_lines)

        return header + escaped_script + footer
