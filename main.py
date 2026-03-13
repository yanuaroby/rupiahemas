#!/usr/bin/env python3
"""
Main entry point for the BloombergTechnoz Financial Script Bot.
Scrapes financial data, generates scripts, and sends via Telegram.
"""

import sys

from src.scraper import BloombergTechnozScraper
from src.summarizer import GroqSummarizer
from src.script_generator import ScriptGenerator
from src.telegram_bot import TelegramSender


def main():
    """Main execution function."""
    print("=" * 50)
    print("BloombergTechnoz Financial Script Bot")
    print("=" * 50)

    try:
        # Check environment variables
        print("\nChecking configuration...")
        from src.config import GROQ_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

        if GROQ_API_KEY:
            print("✓ GROQ_API_KEY is configured")
        else:
            print("✗ GROQ_API_KEY is NOT configured")

        if TELEGRAM_BOT_TOKEN:
            print("✓ TELEGRAM_BOT_TOKEN is configured")
            print(f"  Token length: {len(TELEGRAM_BOT_TOKEN)} chars")
        else:
            print("✗ TELEGRAM_BOT_TOKEN is NOT configured")

        if TELEGRAM_CHAT_ID:
            print("✓ TELEGRAM_CHAT_ID is configured")
            print(f"  Chat ID: {TELEGRAM_CHAT_ID}")
        else:
            print("✗ TELEGRAM_CHAT_ID is NOT configured")

        # Initialize components
        scraper = BloombergTechnozScraper()
        summarizer = GroqSummarizer()
        generator = ScriptGenerator()

        # Pass secrets explicitly to TelegramSender
        print("\nInitializing Telegram bot...")
        telegram = TelegramSender(token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID)

        # Track results
        results = {"rupiah": False, "gold": False}

        # ========== RUPIAH SCRIPT ==========
        print("\n[1/4] Scraping Rupiah data...")
        rupiah_data = scraper.scrape_rupiah()

        if rupiah_data:
            print(f"  ✓ Title: {rupiah_data.title[:50]}...")
            print(f"  ✓ Current Rate: {rupiah_data.current_rate}")
            print(f"  ✓ Trend: {rupiah_data.trend}")

            print("\n[2/4] Generating Rupiah analysis...")
            rupiah_analysis = summarizer.analyze_rupiah(rupiah_data)

            print("\n[3/4] Generating Rupiah script...")
            rupiah_script = generator.generate_rupiah_script(rupiah_data, rupiah_analysis)
            rupiah_message = generator.format_for_telegram(rupiah_script, "Rupiah")

            print("\n[4/4] Sending Rupiah script to Telegram...")
            results["rupiah"] = telegram.send_rupiah_script(rupiah_message)

            if results["rupiah"]:
                print("  ✓ Rupiah script sent successfully!")
            else:
                print("  ✗ Failed to send Rupiah script")
        else:
            print("  ✗ No Rupiah articles found")
            # Send "tidak ada artikel" message
            no_article_msg = "📊 <b>SCRIPT RUPIAH</b> 📊\n\n<b>Tidak ada artikel</b> tentang rupiah yang ditemukan hari ini.\n\n────────────────────\nℹ️ <i>Data dari BloombergTechnoz.com</i>"
            results["rupiah"] = telegram.send_message(no_article_msg)

        # ========== GOLD SCRIPT ==========
        print("\n[1/4] Scraping Gold data...")
        gold_data = scraper.scrape_gold()

        if gold_data:
            print(f"  ✓ Title: {gold_data.title[:50]}...")
            print(f"  ✓ Antam Price: {gold_data.antam_price}")
            print(f"  ✓ Trend: {gold_data.antam_trend}")

            # Use scraped rupiah rate for conversion
            rupiah_rate = rupiah_data.current_rate if rupiah_data else None

            print("\n[2/4] Generating Gold analysis...")
            gold_analysis = summarizer.analyze_gold(gold_data, rupiah_rate)

            print("\n[3/4] Generating Gold script...")
            gold_script = generator.generate_gold_script(gold_data, gold_analysis, rupiah_rate)
            gold_message = generator.format_for_telegram(gold_script, "Gold")

            print("\n[4/4] Sending Gold script to Telegram...")
            results["gold"] = telegram.send_gold_script(gold_message)

            if results["gold"]:
                print("  ✓ Gold script sent successfully!")
            else:
                print("  ✗ Failed to send Gold script")
        else:
            print("  ✗ No Gold articles found")
            # Send "tidak ada artikel" message
            no_article_msg = "📊 <b>SCRIPT GOLD</b> 📊\n\n<b>Tidak ada artikel</b> tentang emas/antam yang ditemukan hari ini.\n\n────────────────────\nℹ️ <i>Data dari BloombergTechnoz.com</i>"
            results["gold"] = telegram.send_message(no_article_msg)

        # ========== SUMMARY ==========
        print("\n" + "=" * 50)
        print("EXECUTION SUMMARY")
        print("=" * 50)
        print(f"Rupiah Script: {'✓ Sent' if results['rupiah'] else '✗ Failed'}")
        print(f"Gold Script: {'✓ Sent' if results['gold'] else '✗ Failed'}")

        # Exit with appropriate code
        if results["rupiah"] or results["gold"]:
            print("\nBot execution completed successfully!")
            sys.exit(0)
        else:
            print("\nBot execution completed with errors.")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error during execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
