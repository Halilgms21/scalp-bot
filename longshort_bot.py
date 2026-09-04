"""
Long/Short Oran Botu - OKX Futures -> Telegram
Ana coinlerdeki long/short pozisyon dengesini izler.
"""

import os
import time
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

# Takip edilecek ana coinler (istersen ekleyip cikarabilirsin)
WATCHLIST = [
    "BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP", "BNB-USDT-SWAP",
    "XRP-USDT-SWAP", "DOGE-USDT-SWAP", "ADA-USDT-SWAP", "AVAX-USDT-SWAP",
    "LINK-USDT-SWAP", "TON-USDT-SWAP", "SUI-USDT-SWAP", "TRX-USDT-SWAP",
]

# Esik degerler: oran bu araligin disina cikarsa uyari gonderilir
HIGH_RATIO_THRESHOLD = 4.0  # longlar cok baskin
LOW_RATIO_THRESHOLD = 0.25  # shortlar cok baskin


def get_long_short_ratio(inst_id: str):
    url = "https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio-contract"
    params = {"instId": inst_id, "period": "5m"}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "0" or not data.get("data"):
        return None
    latest = data["data"][0]
    ratio = float(latest[1])
    return ratio


def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[HATA] Telegram mesaji gonderilemedi: {e}")


def check_ratios():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Long/Short oranlari kontrol ediliyor...")

    for inst_id in WATCHLIST:
        try:
            ratio = get_long_short_ratio(inst_id)
        except Exception as e:
            print(f"[UYARI] {inst_id} icin veri alinamadi: {e}")
            continue

        if ratio is None:
            continue

        print(f"  {inst_id}: oran={ratio:.2f}")

        if ratio >= HIGH_RATIO_THRESHOLD:
            message = (
                f"<b>{inst_id}</b>\n"
                f"Long/Short Orani: {ratio:.2f}\n"
                f"LONGLAR BASKIN - piyasada asiri iyimserlik var.\n"
                f"Bilgi amaclidir, yatirim tavsiyesi degildir."
            )
            send_telegram_message(message)
            print(f"    -> Bildirim gonderildi (yuksek oran)")

        elif ratio <= LOW_RATIO_THRESHOLD:
            message = (
                f"<b>{inst_id}</b>\n"
                f"Long/Short Orani: {ratio:.2f}\n"
                f"SHORTLAR BASKIN - piyasada asiri kotumserlik var.\n"
                f"Bilgi amaclidir, yatirim tavsiyesi degildir."
            )
            send_telegram_message(message)
            print(f"    -> Bildirim gonderildi (dusuk oran)")

        time.sleep(0.3)


if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[UYARI] TELEGRAM_TOKEN veya TELEGRAM_CHAT_ID ayarlanmamis!")
    else:
        check_ratios()
