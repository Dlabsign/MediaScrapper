# MediaScrapper

Alat scraping berita berbasis Python yang mengumpulkan dan mengagregasi artikel berita dari ribuan sumber media resmi melalui Google News RSS. Tanpa memerlukan kunci API AI — scraping murni berbasis RSS dengan analisis kata kunci bawaan.

## Fitur

- **Scraping Murni RSS** — Mengambil berita dari Google News RSS tanpa kunci API atau batasan penggunaan
- **Pencarian Fleksibel** — Cari berdasarkan topik, lokasi, atau keduanya
- **Filter Rentang Waktu** — Filter hasil berdasarkan 24 jam, 7 hari, 30 hari, atau semua waktu
- **Analisis Kata Kunci** — Mengidentifikasi kata kunci yang paling sering muncul dari seluruh artikel yang dikumpulkan
- **Output JSON Terstruktur** — Mengekspor hasil ke file JSON yang rapi dan terformat dengan baik beserta metadata
- **Penyimpanan Otomatis Terorganisir** — File output disimpan dalam folder berbasis tanggal (contoh: `17.07/`) dengan nama file yang deskriptif

## Persyaratan

- **Python 3.10+**
- **Jupyter Notebook** (untuk menjalankan `engine.ipynb`)

### Dependensi Python

| Paket        | Deskripsi                                  |
|--------------|--------------------------------------------|
| `feedparser` | Mengurai feed RSS/Atom dari Google News    |
| `requests`   | Melakukan HTTP request ke endpoint RSS     |

> Modul standar Python yang digunakan: `os`, `re`, `urllib.parse`, `json`, `collections`, `datetime`

## Instalasi

1. **Kloning repositori**

   ```bash
   git clone https://github.com/username-anda/MediaScrapper.git
   cd MediaScrapper
   ```

2. **Instal dependensi**

   ```bash
   pip install feedparser requests
   ```

3. **Buka notebook**

   ```bash
   jupyter notebook engine.ipynb
   ```

## Cara Penggunaan

1. Buka [`engine.ipynb`](engine.ipynb) di Jupyter Notebook
2. Jalankan semua sel. Prompt interaktif akan menanyakan:

   | Prompt | Deskripsi | Contoh |
   |--------|-----------|--------|
   | **Topik Berita** | Topik berita yang ingin dicari | `Kebakaran`, `Korupsi`, `Sepak Bola` |
   | **Lokasi** | Fokus geografis berita | `Bangkok`, `Indonesia`, `Seluruh dunia` |
   | **Rentang Waktu** | `1` = 24 jam, `2` = 7 hari, `3` = 30 hari, `4` = semua waktu | `2` |
   | **Jumlah Maksimal** | Jumlah maksimal artikel yang akan dikumpulkan | `15` |

3. Hasil ditampilkan di konsol dan diekspor ke file JSON secara otomatis

### Struktur Output

Hasil disimpan dalam folder berbasis tanggal dengan konvensi penamaan berikut:

```
DD.MM/scrape_{Topik}_{Lokasi}_{YYYYMMDD}.json
```

**Contoh:** `17.07/scrape_Sepak_Bola_Seluruh_dunia_20260717.json`

File JSON berisi:

```json
{
    "metadata": {
        "total_berita": 15,
        "waktu_ekstraksi": "2026-07-17 13:20:36"
    },
    "berita": [
        {
            "source": "CNN Indonesia",
            "title": "Judul artikel di sini",
            "link": "https://news.google.com/rss/articles/...",
            "published": "Mon, 13 Jul 2026 03:44:42 GMT"
        }
    ],
    "kata_kunci_terpopuler": [
        {
            "peringkat": 1,
            "kata_kunci": "KataKunci",
            "jumlah_kemunculan": 5
        }
    ]
}
```

## Struktur Proyek

```
MediaScrapper/
├── engine.ipynb                                    # Notebook utama berisi logika scraper
├── README.md                                       # Dokumentasi proyek
├── .gitattributes                                  # Konfigurasi Git
├── scrape_Chat_GPT_Amerika_20260717.xlsx           # Contoh output (Excel)
├── scrape_Korupsi_indonesia_20260717.xlsx           # Contoh output (Excel)
└── 17.07/                                          # Folder output berbasis tanggal
    ├── scrape_Kebakaran_bangkok_20260717.json       # Data berita hasil scraping
    ├── scrape_Kereta_api_Indonesia_20260717.json     # Data berita hasil scraping
    └── scrape_Sepak_Bola_Seluruh_dunia_20260717.json # Data berita hasil scraping
```

## Cara Kerja

1. **Konstruksi Query** — Menggabungkan topik dan lokasi yang dimasukkan pengguna menjadi query pencarian, lalu menambahkan filter waktu Google News (`when:1d`, `when:7d`, `when:30d`) jika dipilih
2. **Pengambilan RSS** — Mengirim HTTP GET request ke `https://news.google.com/rss/search` dengan query yang telah di-encode
3. **Parsing Feed** — Menggunakan `feedparser` untuk mengurai respons XML dan mengekstrak judul artikel, sumber, tautan, dan tanggal publikasi
4. **Ekstraksi Kata Kunci** — Melakukan tokenisasi pada semua judul artikel, memfilter kata-kata umum bahasa Indonesia (stop words), dan menghitung frekuensi kata menggunakan `collections.Counter`
5. **Ekspor JSON** — Melakukan serialisasi data yang terkumpul dan analisis kata kunci ke dalam file JSON terstruktur

## Lisensi

Proyek ini bersifat open-source dan tersedia untuk penggunaan pribadi serta edukasi.
