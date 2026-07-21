import concurrent.futures
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote
from flask import Flask, jsonify, render_template, request
import requests
from bs4 import BeautifulSoup
import io
import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def ekstrak_detail_meta(url):
    """Mengambil OpenGraph image & description dari URL artikel asli."""
    foto = "-"
    deskripsi = "-"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Gambar
            og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if og_img and og_img.get("content"):
                foto = og_img["content"]
            else:
                first_img = soup.find("img")
                if first_img and first_img.get("src") and first_img["src"].startswith("http"):
                    foto = first_img["src"]

            # 2. Deskripsi
            og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
            if og_desc and og_desc.get("content"):
                deskripsi = og_desc["content"].strip()
            else:
                paragraphs = soup.find_all("p")
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 40:
                        deskripsi = text
                        break
    except Exception:
        pass
    
    return {"foto": foto, "deskripsi": deskripsi}

def proses_item_berita(item):
    """Memproses 1 item berita RSS dan mengekstrak detailnya."""
    title = item.find('title').text if item.find('title') is not None else 'Tanpa Judul'
    link = item.find('link').text if item.find('link') is not None else '#'
    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else '-'
    
    # Ambil Nama Sumber Berita dari tag <source>
    source_tag = item.find('source')
    sumber_nama = source_tag.text if source_tag is not None else 'Google News'

    # Ekstrak gambar & deskripsi asli via multithreading
    detail = ekstrak_detail_meta(link)

    return {
        "Judul": title,
        "Sumber Nama Website": sumber_nama,
        "Deskripsi Artikel": detail["deskripsi"],
        "Foto": detail["foto"],
        "Sumber": link,
        "Tanggal": pub_date
    }

def scrape_google_news(topik, lokasi, rentang_waktu, max_results):
    """Membentuk Query RSS dan melakukan Scraping."""
    query = topik
    
    # Filter Lokasi
    if lokasi.lower() in ['indonesia', 'id']:
        ceid = "ID:id"
        hl = "id"
        gl = "ID"
    else:
        ceid = "US:en"
        hl = "en-US"
        gl = "US"

    # Filter Rentang Waktu
    if rentang_waktu == "24h":
        query += " when:1d"
    elif rentang_waktu == "7d":
        query += " when:7d"
    elif rentang_waktu == "30d":
        query += " when:30d"

    encoded_query = quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"

    try:
        res = requests.get(rss_url, headers=HEADERS, timeout=10)
        root = ET.fromstring(res.content)
        items = root.findall('./channel/item')[:max_results]

        # Menggunakan ThreadPoolExecutor agar ekstraksi metadata cepat
        berita_list = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = executor.map(proses_item_berita, items)
            for result in results:
                berita_list.append(result)

        return berita_list
    except Exception as e:
        print(f"Error scraping: {e}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def handle_scrape():
    data = request.json
    topik = data.get('topik', 'Teknologi')
    lokasi = data.get('lokasi', 'Indonesia')
    rentang_waktu = data.get('rentang_waktu', 'all')
    max_results = int(data.get('max_results', 15))

    hasil = scrape_google_news(topik, lokasi, rentang_waktu, max_results)
    return jsonify({
        "status": "success",
        "total": len(hasil),
        "berita": hasil
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    
    # ------------------------------- Export Excel
    
@app.route('/api/export/csv', methods=['POST'])
def export_csv():
    data = request.json.get('berita', [])
    if not data:
        return jsonify({"status": "error", "message": "Tidak ada data untuk di-export"}), 400
    
    # Konversi JSON ke DataFrame Pandas
    df = pd.DataFrame(data)
    
    # Pilih dan atur urutan kolom
    df = df[['Judul', 'Sumber Nama Website', 'Deskripsi Artikel', 'Foto', 'Sumber', 'Tanggal']]
    
    # Simpan ke buffer memori sebagai CSV
    output = io.BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='hasil_scraping_berita.csv'
    )

@app.route('/api/export/excel', methods=['POST'])
def export_excel():
    data = request.json.get('berita', [])
    if not data:
        return jsonify({"status": "error", "message": "Tidak ada data untuk di-export"}), 400
    
    df = pd.DataFrame(data)
    df = df[['Judul', 'Sumber Nama Website', 'Deskripsi Artikel', 'Foto', 'Sumber', 'Tanggal']]
    
    # Simpan ke buffer memori sebagai file Excel (.xlsx)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Hasil Scraping', index=False)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='hasil_scraping_berita.xlsx'
    )