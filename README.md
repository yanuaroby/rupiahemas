# BloombergTechnoz Financial Script Bot

Automated financial news scraping and script generation for TikTok/Reels. This bot scrapes Rupiah and Gold (Antam) data from BloombergTechnoz.com, generates structured scripts using LLM, and delivers them via Telegram every weekday at 09:00 AM WIB.

## Features

- 📰 **Web Scraping**: Extracts latest Rupiah and Gold news from BloombergTechnoz.com
- 🤖 **LLM Summarization**: Uses Groq API for intelligent financial analysis
- 📝 **Script Generation**: Formats content into structured TikTok/Reels scripts (Indonesian)
- 📱 **Telegram Delivery**: Sends scripts directly to your Telegram channel
- ⏰ **Automated Scheduling**: Runs Monday-Friday at 09:00 AM WIB via GitHub Actions

## Project Structure

```
rupiahEmas/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration & environment variables
│   ├── scraper.py            # Web scraping module
│   ├── summarizer.py         # Groq LLM integration
│   ├── script_generator.py   # Script template formatting
│   └── telegram_bot.py       # Telegram message sender
├── .github/
│   └── workflows/
│       └── daily_bot.yml     # GitHub Actions schedule
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py
│   └── test_script_generator.py
├── main.py                   # Entry point
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── README.md
```

## Prerequisites

1. **Python 3.9+** installed
2. **Groq API Key** - Get free API key from [Groq Console](https://console.groq.com)
3. **Telegram Bot Token** - Create bot via [@BotFather](https://t.me/BotFather)
4. **Telegram Chat ID** - Your channel/group ID for receiving messages

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rupiahEmas
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
GROQ_API_KEY=your_groq_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

### 5. Test Locally

```bash
python main.py
```

## GitHub Actions Setup

### 1. Add Secrets to Repository

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `GROQ_API_KEY` | Your Groq API key |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |

### 2. Workflow Schedule

The bot runs automatically:
- **Schedule**: Monday-Friday at 02:00 UTC (09:00 WIB)
- **Manual Trigger**: You can also run manually via Actions tab

## Script Templates

### Rupiah Script Format

```
JUDUL : [Title from website]

Nilai tukar rupiah melemah/menguat dalam pembukaan perdagangan hari ini. 
[Hari], [Tanggal], rupiah dihargai [Nilai]/US$. Kemudian pada pukul [Waktu] WIB, 
rupiah bergerak ke angka [Nilai]/US$.

NILAI TUKAR RUPIAH [Nilai]/US$ [Melemah/Menguat] [X]% dari sebelumnya

[2-4 Kalimat Analisis Faktor Eksternal]

NILAI TUKAR MATA UANG ASIA [List Mata Uang & Persentase]

[2-4 Kalimat Analisis Global/Domestik]

PERKIRAAN PELEMAHAN RUPIAH [Range Harga]
```

### Gold Script Format

```
JUDUL : [Title from website]

Harga emas PT Aneka Tambang Tbk atau Antam naik/turun/stagnan. 
HARGA EMAS ANTAM [Tanggal] Rp [Harga]/gram. [Naik/Turun] Rp [Nilai]/gram dari hari sebelumnya

HARGA BUYBACK EMAS ANTAM Rp [Harga]/gram. [Naik/Turun] Rp [Nilai]/gram dari sebelumnya

[2 Kalimat korelasi emas dunia]

HARGA EMAS DUNIA US$ [Nilai]/troy ons. Rp. [Konversi] [Bertambah/Berkurang] [X]% dari hari sebelumnya

[2 Kalimat alasan kenaikan/penurunan]

PERKIRAAN KENAIKAN HARGA EMAS DUNIA US$ [Range] atau Rp. [Konversi] hingga US$ [Range] atau Rp. [Konversi]
```

## Getting Telegram Chat ID

### For Private Channel:
1. Add your bot to the channel as admin
2. Send a message to the channel
3. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Look for `"chat":{"id":-100xxxxxxxxxx}`

### For Group:
1. Add your bot to the group
2. Send `/start` in the group
3. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Look for the chat ID

### For Private Chat:
1. Start a chat with your bot
2. Send `/start`
3. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Look for `"chat":{"id":xxxxxxxxx}`

## Troubleshooting

### Bot not sending messages
- Verify bot token is correct
- Ensure bot is added to channel/group as admin
- Check chat ID format (channels need `-100` prefix)

### Scraping fails
- Website structure may have changed
- Check network connectivity
- Review scraper selectors in `src/scraper.py`

### Groq API errors
- Verify API key is valid
- Check API rate limits
- Ensure free tier quota is available

## License

MIT License - Feel free to use and modify.

## Disclaimer

This bot is for educational purposes. Financial data should be verified before making investment decisions.
