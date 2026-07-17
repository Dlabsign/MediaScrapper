"""
Scraper Tweet Berita Berdasarkan Keyword/Hashtag (X / Twitter)
================================================================
Menggunakan library unofficial `twikit` (gratis, login pakai akun X biasa,
TANPA butuh API key berbayar).

⚠️ PENTING:
- Ini melanggar Terms of Service X. Gunakan akun sekunder, bukan akun utama,
  untuk menghindari risiko suspend/rate-limit pada akun pribadi.
- Jangan scraping terlalu agresif / dalam volume besar. Skrip ini sudah diberi
  delay antar request untuk mengurangi risiko deteksi bot.
- Cocok untuk riset/monitoring skala kecil-menengah.

INSTALASI:
    pip install twikit --break-system-packages

CARA PAKAI:
1. Isi kredensial akun X kamu di bagian CONFIG di bawah (atau lewat environment
   variable, lihat komentar).
2. Ubah SEARCH_QUERY sesuai keyword/hashtag yang ingin dicari.
3. Jalankan: python scrape_x_news.py
4. Hasil akan tersimpan di file `hasil_scrape.csv` dan `hasil_scrape.json`.

Setelah login pertama kali berhasil, twikit akan menyimpan cookies ke
`cookies.json` supaya login berikutnya lebih cepat dan tidak perlu
memasukkan password ulang setiap kali (mengurangi risiko flagging).
"""

import asyncio
import csv
import json
import os
import re
from datetime import datetime

from twikit import Client

# ============================================================
# CONFIG — sesuaikan bagian ini
# ============================================================
USERNAME = os.getenv("X_USERNAME", "username_kamu")
EMAIL = os.getenv("X_EMAIL", "email_kamu@example.com")
PASSWORD = os.getenv("X_PASSWORD", "password_kamu")

SEARCH_QUERY = "#banjirjakarta"   # ganti dengan keyword/hashtag yang dicari
SEARCH_MODE = "Latest"            # "Latest" (terbaru) atau "Top" (populer)
MAX_TWEETS = 100                  # batas jumlah tweet yang mau diambil
DELAY_BETWEEN_PAGES = 3           # detik, jeda antar halaman (anti rate-limit)

COOKIES_FILE = "cookies.json"
OUTPUT_CSV = "hasil_scrape.csv"
OUTPUT_JSON = "hasil_scrape.json"


def extract_links(text: str):
    """Ambil semua URL dari teks tweet."""
    return re.findall(r"https?://\S+", text or "")


def extract_hashtags(text: str):
    """Ambil semua hashtag dari teks tweet."""
    return re.findall(r"#(\w+)", text or "")


def extract_media(tweet):
    """
    Ambil URL media (foto/video) dari objek tweet twikit.
    Video di twikit biasanya berupa beberapa variant bitrate;
    kita ambil variant dengan bitrate tertinggi (kualitas terbaik).
    """
    media_urls = []
    media_list = getattr(tweet, "media", None) or []
    for m in media_list:
        media_type = getattr(m, "type", None)
        if media_type == "photo":
            url = getattr(m, "media_url_https", None) or getattr(m, "url", None)
            if url:
                media_urls.append({"type": "photo", "url": url})
        elif media_type in ("video", "animated_gif"):
            variants = getattr(m, "video_info", {}).get("variants", []) if hasattr(m, "video_info") else []
            best = None
            best_bitrate = -1
            for v in variants:
                if v.get("content_type") == "video/mp4" and v.get("bitrate", 0) > best_bitrate:
                    best = v.get("url")
                    best_bitrate = v.get("bitrate", 0)
            if best:
                media_urls.append({"type": media_type, "url": best})
    return media_urls


async def login_client() -> Client:
    client = Client("en-US")

    if os.path.exists(COOKIES_FILE):
        print("[i] Menggunakan cookies tersimpan, tidak perlu login ulang...")
        client.load_cookies(COOKIES_FILE)
    else:
        print("[i] Login pertama kali dengan username/email/password...")
        await client.login(
            auth_info_1=USERNAME,
            auth_info_2=EMAIL,
            password=PASSWORD,
        )
        client.save_cookies(COOKIES_FILE)
        print(f"[i] Cookies disimpan ke {COOKIES_FILE} untuk login berikutnya.")

    return client


async def scrape_tweets():
    client = await login_client()

    print(f"[i] Mencari tweet untuk query: '{SEARCH_QUERY}' (mode: {SEARCH_MODE})")
    results = await client.search_tweet(SEARCH_QUERY, product=SEARCH_MODE)

    collected = []
    page = 1

    while results and len(collected) < MAX_TWEETS:
        print(f"[i] Memproses halaman {page}, tweet terkumpul sejauh ini: {len(collected)}")

        for tweet in results:
            text = tweet.text or ""
            row = {
                "tweet_id": tweet.id,
                "username": tweet.user.screen_name if tweet.user else None,
                "display_name": tweet.user.name if tweet.user else None,
                "created_at": str(tweet.created_at),
                "text": text,
                "likes": tweet.favorite_count,
                "retweets": tweet.retweet_count,
                "replies": tweet.reply_count,
                "hashtags": extract_hashtags(text),
                "links": extract_links(text),
                "media": extract_media(tweet),
                "tweet_url": f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}" if tweet.user else None,
            }
            collected.append(row)

            if len(collected) >= MAX_TWEETS:
                break

        if len(collected) >= MAX_TWEETS:
            break

        # Ambil halaman berikutnya (pagination)
        try:
            await asyncio.sleep(DELAY_BETWEEN_PAGES)
            results = await results.next()
            page += 1
        except Exception as e:
            print(f"[!] Tidak bisa lanjut ke halaman berikutnya: {e}")
            break

    return collected


def save_results(data):
    # Simpan JSON (menyimpan struktur lengkap, termasuk list media/hashtags/links)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[✓] {len(data)} tweet disimpan ke {OUTPUT_JSON}")

    # Simpan CSV (list diratakan jadi string dipisah ' | ')
    if data:
        fieldnames = list(data[0].keys())
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                flat_row = row.copy()
                flat_row["hashtags"] = " | ".join(row["hashtags"])
                flat_row["links"] = " | ".join(row["links"])
                flat_row["media"] = " | ".join(m["url"] for m in row["media"])
                writer.writerow(flat_row)
        print(f"[✓] {len(data)} tweet disimpan ke {OUTPUT_CSV}")


async def main():
    print(f"=== Mulai scraping — {datetime.now().isoformat()} ===")
    data = await scrape_tweets()
    save_results(data)
    print("=== Selesai ===")


if __name__ == "__main__":
    asyncio.run(main())