"""
Funding Rate Sinyal Botu - OKX Futures -> Telegram (tek seferlik calisir)
"""

import os
import time
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "BURAYA_TOKEN_YAZ").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "BURAYA_CHAT_ID_YAZ").strip()

FUNDING_RATE_THRESHOLD = 0.02
SYMBOLS = []


def get_usdt_swap_instruments():
    url = "https://www.okx.com/api/v5/public/instruments"
    params = {"instType": "SWAP"}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "0":
        raise Exception(f"OKX instruments hatasi: {data.get('msg')}")

    instruments = []
    for item in data["data"]:
        inst_id = item["instId"]
        if not inst_id.endswith("-USDT-SWAP"):
            continue
        if SYMBOLS and inst_id not in SYMBOLS:
            continue
        instruments.append(inst_id)
    return instruments


def get_funding_rate(inst_id: str):
    url = "https://www.okx.com/api/v5/public/funding-rate"
    params = {"instId": inst_id}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "0" or not data.get("data"):
        return None

    item = data["data"][0]
    funding_rate = float(item["fundingRate"]) * 100
    next_funding_time = int(item.get("nextFundingTime", 0))
    return {
        "symbol": inst_id,
        "funding_rate": funding_rate,
        "next_funding_time": next_funding_time,
    }


def get_all_funding_rates():
    instruments = get_usdt_swap_instruments()
    print(f"{len(instruments)} adet USDT-SWAP coin bulundu, taraniyor...")

    results = []
    for inst_id in instruments:
        try:
            rate_info = get_funding_rate(inst_id)
            if rate_info:
                results.append(rate_info)
        except Exception as e:
            print(f"[UYARI] {inst_id} icin veri alinamadi: {e}")
        time.sleep(0.15)
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
    if not timestamp_ms:
        return "bilinmiyor"
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
