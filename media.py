# ==================================================================
# CARA MENJALANKAN SCRIPT INI:
# 1. Install library yang dibutuhkan via terminal/cmd:
#    pip install feedparser requests
# 2. Jalankan script:
#    python nama_file.py
# ==================================================================

import os
import re
import urllib.parse
import json
import requests
import feedparser
from collections import Counter
from datetime import datetime

# ------------------------------------------------------------------
# Konfigurasi Dasar
# ------------------------------------------------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Daftar kata yang akan diabaikan dalam analisis kata kunci terpopuler
STOPWORDS = set("""
yang untuk dengan dari pada ke di dan atau ini itu akan telah para
sudah tidak bisa ada juga karena setelah oleh saat jadi lebih masih
namun hingga sebagai dalam soal terkait usai kata jelang adalah
bahwa ia kami mereka dia kamu saya kita untuknya dari-nya ke-nya
""".split())


def clean_title(title: str) -> list[str]:
    """Mengambil kata-kata bermakna dari judul berita untuk dihitung frekuensinya."""
    # Cari kata yang memiliki panjang minimal 4 karakter
    words = re.findall(r"[a-zA-ZÀ-ÿ]{4,}", title.lower())
    return [w for w in words if w not in STOPWORDS]


def fetch_news_pure_scraping(topic: str, location: str, time_range_code: str, max_results: int):
    """Mencari berita dari ribuan media resmi terpercaya via Google News RSS."""
    
    # Gabungkan kueri pencarian dasar
    search_query = f"{topic} {location}".strip()
    
    # Tambahkan filter waktu Google News jika dipilih
    if time_range_code == "1":
        search_query += " when:1d"  # 24 jam terakhir
    elif time_range_code == "2":
        search_query += " when:7d"  # 7 hari terakhir
    elif time_range_code == "3":
        search_query += " when:30d" # 30 hari terakhir
    
    # Melakukan URL Encoding agar aman dikirim sebagai parameter
    encoded_query = urllib.parse.quote(search_query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=id&gl=ID&ceid=ID:id"
    
    all_entries = []
    try:
        print(f"\n[PROSES] Menghubungkan ke server agregator berita...")
        resp = requests.get(rss_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        
        feed = feedparser.parse(resp.content)
        
        # Batasi jumlah berita yang diambil sesuai permintaan user
        news_items = feed.entries[:max_results] if max_results > 0 else feed.entries

        for entry in news_items:
            title_raw = entry.get("title", "").strip()
            source_name = "Media Resmi"
            title_clean = title_raw
            
            # Google News biasanya menyertakan nama media di akhir judul ("Judul - Nama Media")
            # Kita pisahkan agar kolom Judul dan kolom Sumber Media terpisah rapi
            if " - " in title_raw:
                parts = title_raw.split(" - ")
                source_name = parts[-1]
                title_clean = " - ".join(parts[:-1])

            all_entries.append({
                "source": source_name,
                "title": title_clean,
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
            })
            
        print(f"[SUKSES] Berhasil mengumpulkan {len(all_entries)} berita resmi.")
    except Exception as e:
        print(f"[GAGAL] Proses scraping berita mengalami masalah: {e}")
        
    return all_entries


def analyze_keywords(entries, top_n=15):
    """Menganalisis kata kunci/topik yang paling sering muncul dari judul berita secara lokal."""
    counter = Counter()
    for e in entries:
        counter.update(clean_title(e["title"]))
    return counter.most_common(top_n)


def export_to_json(entries, keywords, filepath):
    """Menyimpan seluruh berita dan analisis kata kunci ke dalam file format JSON terstruktur."""
    
    # Bungkus data ke dalam skema JSON terstruktur
    output_data = {
        "metadata": {
            "total_berita": len(entries),
            "waktu_ekstraksi": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "berita": entries,
        "kata_kunci_terpopuler": [
            {
                "peringkat": index,
                "kata_kunci": word.capitalize(),
                "jumlah_kemunculan": count
            }
            for index, (word, count) in enumerate(keywords, start=1)
        ]
    }
    
    try:
        # Menulis data ke file JSON dengan encoding UTF-8 agar karakter spesial tetap aman
        with open(filepath, "w", encoding="utf-8") as json_file:
            json.dump(output_data, json_file, indent=4, ensure_ascii=False)
        print(f"[SUKSES] Seluruh data hasil scraping berhasil diexport ke: {filepath}")
    except Exception as e:
        print(f"[GAGAL] Proses export ke file JSON mengalami kendala: {e}")


def main():
    print("=" * 65)
    print("      PURE SC-NEWS SCRAPER (BEBAS LIMIT - TANPA AI API)      ")
    print("=" * 65)
    
    # 1. Input Kriteria Pencarian Berita
    topic = input("1. Masukkan Topik Berita (contoh: 'Kebakaran', 'Korupsi'): ").strip()
    location = input("2. Masukkan Lokasi (contoh: 'Bangkok', 'Indonesia'): ").strip()
    
    if not topic:
        print("[EROR] Topik berita minimal harus diisi!")
        return

    # 2. Input Rentang Waktu Pencarian
    print("\nPilih Rentang Waktu Berita:")
    print("  [1] 24 Jam Terakhir")
    print("  [2] 7 Hari Terakhir")
    print("  [3] 30 Hari Terakhir")
    print("  [4] Semua Waktu (Tanpa Batasan)")
    time_choice = input("3. Masukkan pilihan rentang waktu (1/2/3/4) [Default 4]: ").strip()
    if time_choice not in ["1", "2", "3", "4"]:
        time_choice = "4"

    # 3. Input Batas Jumlah Berita
    limit_input = input("\n4. Masukkan jumlah maksimal berita yang ingin diambil [Default 15]: ").strip()
    max_results = int(limit_input) if limit_input.isdigit() else 15

    print("\n" + "-" * 65)
    print(f"[PROSES] Memulai scraping berita tentang '{topic}' di '{location}'...")
    
    # Eksekusi Scraping Murni
    entries = fetch_news_pure_scraping(topic, location, time_choice, max_results)
    
    if not entries:
        print("\n" + "!" * 65)
        print("[INFO] Tidak ditemukan berita valid dari situs resmi untuk kriteria tersebut.")
        print("!" * 65)
        return

    # Analisis kata kunci populer secara lokal
    keywords = analyze_keywords(entries)

    print(f"\n[OK] Berhasil mengumpulkan {len(entries)} berita.")
    print("-" * 65)
    
    # Tampilkan 5 berita teratas langsung di terminal sebagai tinjauan cepat
    print("CONTOH BERITA TERBARU YANG DITEMUKAN:")
    for idx, item in enumerate(entries[:5], start=1):
        print(f" {idx}. [{item['source']}] {item['title']}")
        print(f"    Link: {item['link']}\n")

    # 1. Tentukan Nama Folder Baru berdasarkan waktu saat ini -> format (DD.MM)
    folder_name = datetime.now().strftime("%d.%m")
    
    # Buat direktori/folder jika belum ada
    os.makedirs(folder_name, exist_ok=True)

    # 2. Buat Nama File secara dinamis dengan format ekstensi .json
    clean_filename = re.sub(r'[^a-zA-Z0-9]', '_', f"{topic}_{location}".strip("_"))
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"scrape_{clean_filename}_{date_str}.json"
    
    # Gabungkan folder dan file menjadi path lengkap (contoh: 17.07/scrape_Korupsi_Indonesia_20260717.json)
    filepath = os.path.join(folder_name, filename)
    
    # Ekspor ke file JSON di dalam folder tersebut
    export_to_json(entries, keywords, filepath)


if __name__ == "__main__":
    main()