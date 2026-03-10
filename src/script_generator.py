"""
Script generator module for formatting financial scripts.
Generates Rupiah and Gold scripts following the specified templates.
"""

from datetime import datetime
from typing import Optional

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

    def _generate_catchy_rupiah_title(self, original_title: str, trend: str, percentage: float) -> str:
        """Generate a catchy title for Rupiah script that attracts viewers."""
        trend_word = "MELEMAH" if trend == "melemah" else "MENGUAT" if trend == "menguat" else "BERGEJOLAK"
        pct_abs = abs(percentage) if percentage else 0
        
        # Create attention-grabbing title
        if pct_abs >= 0.5:
            return f"RUPIAH {trend_word} {pct_abs:.2f}%! INI PENYEBAB UTAMANYA"
        elif pct_abs > 0:
            return f"RUPIAH {trend_word} {pct_abs:.2f}%, PENGAMAT BILANG INI DIA PENYEBABNYA"
        else:
            return f"RUPIAH STAGNAN, ANALIS PREDIKSI AKAN GERAK KE ARAH INI"

    def generate_rupiah_script(
        self, data: RupiahData, analysis: RupiahAnalysis
    ) -> str:
        """
        Generate Rupiah script following the new template.

        Template:
        JUDUL : (judul tegas & menarik)

        Nilai tukar rupiah melemah dalam pembukaan perdagangan hari ini

        Pada (tanggal) rupiah dihargai Rp(berapa)/US$

        Kemudian pada pukul (waktu) WIB, rupiah berada di angka Rp(berapa)/US$

        NILAI TUKAR RUPIAH (tanggal)

        Rp(berapa)/US$
        Melemah/Menguat (berapa)% dari sebelumnya

        ****
        (konteks 1-5)

        NILAI TUKAR MATA UANG ASIA (tanggal)

        (mata uang negara) melemah/menguat (berapa)%.

        PERKIRAAN PELEMAHAN RUPIAH (tanggal)

        Rp(berapa) Hingga Rp(berapa).
        """
        day_name, date_str = self._get_current_day_date()

        # Get values with fallbacks
        current_rate = data.current_rate or data.opening_rate or 16000
        opening_rate = data.opening_rate or current_rate
        time_wib = data.time_wib or "10:00"
        percentage = data.percentage_change if data.percentage_change is not None else 0
        trend = data.trend or "melemah"

        # Generate catchy title
        catchy_title = self._generate_catchy_rupiah_title(data.title, trend, percentage)

        # Format percentage with Indonesian decimal separator
        pct_formatted = f"{abs(percentage):.2f}".replace(".", ",")

        # Format Asian currencies section
        asian_currencies_section = self._format_asian_currencies_section(analysis.asian_currencies, date_str)

        # Format the script
        script = f"""JUDUL : {catchy_title}

Nilai tukar rupiah {trend} dalam pembukaan perdagangan hari ini

Pada {date_str} rupiah dihargai Rp{self._format_number(opening_rate)}/US$

Kemudian pada pukul {time_wib} WIB, rupiah berada di angka Rp{self._format_number(current_rate)}/US$

NILAI TUKAR RUPIAH {date_str}

Rp{self._format_number(current_rate)}/US$
{trend.capitalize()} {pct_formatted}% dari sebelumnya

****
{analysis.context_1}

{analysis.context_2}

{analysis.context_3}

{analysis.context_4}

{analysis.context_5}

{asian_currencies_section}
PERKIRAAN PELEMAHAN RUPIAH {date_str}

Rp{analysis.forecast_low} Hingga Rp{analysis.forecast_high}."""

        return script.strip()

    def _format_asian_currencies_section(self, asian_currencies: list, date_str: str) -> str:
        """Format Asian currencies section with each currency on separate line."""
        if not asian_currencies:
            return f"NILAI TUKAR MATA UANG ASIA {date_str}\n\nData mata uang Asia tidak tersedia."
        
        header = f"NILAI TUKAR MATA UANG ASIA {date_str}\n\n"
        lines = []
        
        for currency in asian_currencies:
            name = currency.get('name', 'Mata Uang')
            change_pct = currency.get('change_pct', 0)
            trend = currency.get('trend', 'melemah' if change_pct < 0 else 'menguat')
            
            # Format percentage with Indonesian decimal separator
            pct_formatted = f"{abs(change_pct):.2f}".replace(".", ",")
            
            lines.append(f"{name} {trend} {pct_formatted}%.")
        
        return header + "\n".join(lines)

    def _generate_gold_title(
        self, antam_trend: str, antam_change: float
    ) -> str:
        """Generate simplified gold title like 'EMAS ANTAM NAIK RP28.000/GRAM, HARI INI'."""
        trend_upper = "NAIK" if antam_trend == "naik" else "TURUN" if antam_trend == "turun" else "STAGNAN"
        change_formatted = self._format_number(int(antam_change))
        return f"EMAS ANTAM {trend_upper} RP{change_formatted}/GRAM, HARI INI"

    def generate_gold_script(
        self, data: GoldData, analysis: GoldAnalysis, rupiah_rate: Optional[float] = None
    ) -> str:
        """
        Generate Gold script following the template.

        Template:
        JUDUL : EMAS ANTAM NAIK RP28.000/GRAM, HARI INI

        Harga emas PT Aneka Tambang Tbk atau Antam kembali naik

        HARGA EMAS ANTAM
        Rp 2.944.000/gram.
        Naik Rp28.000/gram dari hari sebelumnya

        HARGA BUYBACK EMAS ANTAM
        Rp 2.725.000/gram.
        Turun Rp31.000/gram dari hari sebelumnya

        ****
        Korelasi text...

        HARGA EMAS DUNIA 20 FEBRUARI 2026
        US$ 4.997,7/troy ons.
        Rp84.408.733
        Bertambah 0,43% dari hari sebelumnya

        Catalyst text...

        PERKIRAAN KENAIKAN HARGA EMAS DUNIA
        US$ 5.006/troy ons atau Rp. 84.548.916
        hingga
        US$ 5.082/troy ons atau Rp. 85.832.519

        *****END
        """
        # Get values with fallbacks
        antam_price = data.antam_price or 1_000_000
        antam_change = data.antam_change if data.antam_change else 0
        antam_trend = data.antam_trend or "stagnan"

        buyback_price = data.buyback_price or int(antam_price * 0.9)
        buyback_change = data.buyback_change if data.buyback_change else int(antam_change * 0.9)

        # Calculate buyback trend independently
        if buyback_change > 0:
            buyback_trend = "naik"
        elif buyback_change < 0:
            buyback_trend = "turun"
        else:
            buyback_trend = "stagnan"

        # Use absolute values for display
        antam_change_abs = abs(antam_change)
        buyback_change_abs = abs(buyback_change)

        global_gold = data.global_gold_usd or 2000
        global_change_pct = data.global_gold_change_pct if data.global_gold_change_pct else 0

        # Calculate IDR conversion for global gold
        # 1 troy oz = 31.1035 grams
        if rupiah_rate:
            global_gold_idr = int(global_gold * rupiah_rate / 31.1035)
        else:
            global_gold_idr = int(global_gold * 16000 / 31.1035)

        # Determine trend words for Antam
        antam_trend_action = "Naik" if antam_trend == "naik" else "Turun" if antam_trend == "turun" else "Stagnan"
        antam_intro = "kembali naik" if antam_trend == "naik" else "kembali turun" if antam_trend == "turun" else "stagnan"

        # Determine trend words for buyback
        buyback_trend_action = "Naik" if buyback_trend == "naik" else "Turun" if buyback_trend == "turun" else "Stagnan"

        # Determine trend word for global gold
        global_trend_word = "Bertambah" if global_change_pct >= 0 else "Berkurang"
        global_change_pct_abs = abs(global_change_pct)

        # Generate simplified title
        title = self._generate_gold_title(antam_trend, antam_change_abs)

        # Build Antam price section - only show change line if there's a change
        antam_price_section = f"Rp {self._format_number(antam_price)}/gram."
        if antam_change_abs > 0:
            antam_price_section += f"\n{antam_trend_action} Rp{self._format_number(antam_change_abs)}/gram dari hari sebelumnya"

        # Build Buyback price section - only show change line if there's a change
        buyback_price_section = f"Rp {self._format_number(buyback_price)}/gram."
        if buyback_change_abs > 0:
            buyback_price_section += f"\n{buyback_trend_action} Rp{self._format_number(buyback_change_abs)}/gram dari sebelumnya"

        # Format the script with proper structure
        script = f"""JUDUL : {title}

Harga emas PT Aneka Tambang Tbk atau Antam {antam_intro}

HARGA EMAS ANTAM

{antam_price_section}

HARGA BUYBACK EMAS ANTAM

{buyback_price_section}

****
{analysis.global_correlation}

HARGA EMAS DUNIA {data.date.upper() if data.date else ''}

US$ {self._format_number(global_gold, 1)}/troy ons.
Rp{self._format_number(global_gold_idr)}
{global_trend_word} {self._format_number(global_change_pct_abs, 2).replace('.', ',')}% dari hari sebelumnya

{analysis.price_catalysts}

PERKIRAAN KENAIKAN HARGA EMAS DUNIA

{analysis.forecast_range_usd} atau {analysis.forecast_range_idr}"""

        return script.strip()

    def format_for_telegram(self, script: str, script_type: str) -> str:
        """Format script for Telegram message with HTML styling."""
        header = f"📊 <b>SCRIPT {script_type.upper()}</b> 📊\n\n"
        footer = "\n\n────────────────────\nℹ️ <i>Data dari BloombergTechnoz.com</i>"

        # Remove separator lines before processing
        script = script.replace("****", "")

        # Escape HTML special characters
        escaped_script = script.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Handle bold titles (JUDUL : ...)
        import re
        escaped_script = re.sub(r'JUDUL : (.+)', r'<b>JUDUL : \1</b>', escaped_script)

        # Handle section headers (ALL CAPS lines)
        lines = escaped_script.split('\n')
        formatted_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.isupper() and len(stripped) > 3:
                formatted_lines.append(f"<b>{stripped}</b>")
            else:
                formatted_lines.append(line)
        escaped_script = '\n'.join(formatted_lines)

        return header + escaped_script + footer
