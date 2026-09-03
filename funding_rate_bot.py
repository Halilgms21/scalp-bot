"""
Funding Rate Sinyal Botu - Binance Futures -> Telegram (tek seferlik calisir)
"""

import os
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "BURAYA_TOKEN_YAZ")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "BURAYA_CHAT_ID_YAZ")

FUNDING_RATE_THRESHOLD = 0.02

SYMBOLS = []


def get_all_funding_rates():
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data:
        symbol = item["symbol"]
        if SYMBOLS and symbol not in SYMBOLS:
            continue
        funding_rate = float(item["lastFundingRate"]) * 100
        mark_price = float(item["markPrice"])
        next_funding_time = int(item["nextFundingTime"])
        results.append({
            "symbol": symbol,
            "funding_rate": funding_rate,
            "mark_price": mark_price,
            "next_funding_time": next_funding_time,
        })
    return results


def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[HATA] Telegram mesaji gonderilemedi: {e}")


def format_next_funding_time(timestamp_ms: int) -> str:
    dt = datetime.utcfromtimestamp(timestamp_ms / 1000)
    return dt.strftime("%H:%M UTC")


def check_funding_rates():
    try:
        rates = get_all_funding_rates()
    except Exception as e:
        print(f"[HATA] Funding rate verisi cekilemedi: {e}")
        return

    alerts = [r for r in rates if abs(r["funding_rate"]) >= FUNDING_RATE_THRESHOLD]
    alerts.sort(key=lambda r: abs(r["funding_rate"]), reverse=True)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
          f"{len(rates)} coin tarandi, {len(alerts)} tanesi esigi asti.")

    for r in alerts:
        direction = "POZITIF (Longlar oduyor)" if r["funding_rate"] > 0 \
            else "NEGATIF (Shortlar oduyor)"
        message = (
            f"<b>{r['symbol']}</b>\n"
            f"Funding Rate: {r['funding_rate']:.4f}%\n"
            f"{direction}\n"
            f"Mark Price: {r['mark_price']}\n"
            f"Sonraki Funding: {format_next_funding_time(r['next_funding_time'])}\n"
            f"Bu bir otomatik sinyaldir, yatirim tavsiyesi degildir."
        )
        send_telegram_message(message)
        print(f"  -> Bildirim gonderildi: {r['symbol']} ({r['funding_rate']:.4f}%)")


if __name__ == "__main__":
    if TELEGRAM_TOKEN == "BURAYA_TOKEN_YAZ":
        print("[UYARI] TELEGRAM_TOKEN ayarlanmamis!")
    else:
        check_funding_rates()
