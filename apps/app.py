import os
import io
import concurrent.futures
import xml.etree.ElementTree as ET
from urllib.parse import quote
from flask import Flask, jsonify, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
import pandas as pd
from google import genai

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Masukkan Gemini API Key Anda di sini atau via Environment Variable
# GEMINI_API_KEY = "AQ.Ab8RN6IJ26P7-uz-0lcdwpXLe0jT-2ddaFZXwA60tvDWVNvtwQ"
GEMINI_API_KEY = "AIzaSyBKFdWcvr2BOkVKTSc5YbZ-h5ZK2l4knYo"

def get_gemini_client():
    if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
        return genai.Client(api_key=GEMINI_API_KEY)
    return None

def ekstrak_detail_meta(url):
    """Mengambil description dari URL artikel asli."""
    deskripsi = "-"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
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
    
    return {"deskripsi": deskripsi}

def proses_item_berita(item):
    """Memproses 1 item berita RSS."""
    title = item.find('title').text if item.find('title') is not None else 'Tanpa Judul'
    link = item.find('link').text if item.find('link') is not None else '#'
    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else '-'
    
    source_tag = item.find('source')
    sumber_nama = source_tag.text if source_tag is not None else 'Google News'

    detail = ekstrak_detail_meta(link)

    return {
        "Judul": title,
        "Sumber Nama Website": sumber_nama,
        "Deskripsi Artikel": detail["deskripsi"],
        "Sumber": link,
        "Tanggal": pub_date,
        "Caption": ""  # Default kosong
    }

def scrape_google_news(topik, lokasi, rentang_waktu, max_results):
    query = topik
    if lokasi.lower() in ['indonesia', 'id']:
        ceid, hl, gl = "ID:id", "id", "ID"
    else:
        ceid, hl, gl = "US:en", "en-US", "US"

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
    return render_template('index2.html')

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

# --- ENDPOINT AI GEMINI CAPTION GENERATOR ---
@app.route('/api/generate-caption', methods=['POST'])
def generate_caption():
    data = request.json
    judul = data.get('judul', '')
    deskripsi = data.get('deskripsi', '')
    sumber = data.get('sumber', '')

    if not judul:
        return jsonify({"status": "error", "message": "Judul berita tidak ditemukan"}), 400

    prompt = f"""Kamu adalah seorang Social Media Specialist & Content Creator profesional.
Buatkan caption media sosial dalam bahasa Indonesia yang formal, lugas, dan mudah dipahami oleh audiens berusia 18 hingga 40 tahun berdasarkan berita berikut:

Judul Berita: {judul}
Deskripsi/Ringkasan: {deskripsi}
Sumber Media: {sumber}

Ketentuan Penulisan:
1. DILARANG MENGGUNAKAN format Markdown seperti cetak tebal (contoh: **teks**), cetak miring (*teks*), atau simbol tanda bintang (*). Tulis dalam bentuk teks polos (plain text) biasa.
2. DILARANG MENGGUNAKAN emoji, ikon, atau simbol dekoratif apa pun di seluruh isi caption.
3. Panjang caption MAKSIMAL 3 PARAGRAF singkat:
   - Paragraf 1: Kalimat pembuka (hook) yang memikat perhatian namun tetap bernuansa formal.
   - Paragraf 2 & 3: Rangkuman inti berita yang padat, informatif, dan mudah dipahami.
4. Gunakan bahasa formal yang komunikatif, rapi, dan profesional (tidak terlalu santai/gaul, namun tidak kaku).
5. DILARANG KERAS menyertakan kalimat pertanyaan interaktif, ajakan diskusi, atau arahan komentar di bagian akhir (seperti "Bagaimana menurutmu?", "Tulis di kolom komentar", dll).
6. Di bagian paling bawah (setelah paragraf), WAJIB menyertakan tepat 5 hashtag dipisahkan spasi tanpa tanda kurung/placeholder:
   #dlabsign.news #beritaindonesia [3 hashtag spesifik & relevan lainnya dengan topik berita]

Output langsung berupa teks caption saja tanpa kata pengantar, salam, atau penjelasan dari AI.
"""

    try:
        client = get_gemini_client()
        if not client:
            return jsonify({"status": "error", "message": "Gemini API Key belum dikonfigurasi di server (GEMINI_API_KEY)."}), 500

        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=prompt,
        )
        
        return jsonify({
            "status": "success",
            "caption": response.text.strip()
        })
    except Exception as e:
        print(f"Error Gemini API: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ENDPOINT EXPORT EXCEL ---
@app.route('/api/export/excel', methods=['POST'])
def export_excel():
    data = request.json.get('berita', [])
    if not data:
        return jsonify({"status": "error", "message": "Tidak ada data untuk di-export"}), 400
    
    df = pd.DataFrame(data)
    
    # Kolom yang akan diekspor ke Excel (tanpa foto, menyertakan Caption AI)
    cols = ['Judul', 'Sumber Nama Website', 'Deskripsi Artikel', 'Caption', 'Sumber', 'Tanggal']
    for col in cols:
        if col not in df.columns:
            df[col] = ''
            
    df = df[cols]
    df.rename(columns={
        'Sumber Nama Website': 'Sumber Media',
        'Caption': 'Caption AI (Sosmed)'
    }, inplace=True)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Berita & Caption AI', index=False)
        
        # Format lebar kolom otomatis
        worksheet = writer.sheets['Berita & Caption AI']
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)

    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='hasil_berita_dan_caption.xlsx'
    )

@app.route('/api/export/csv', methods=['POST'])
def export_csv():
    data = request.json.get('berita', [])
    if not data:
        return jsonify({"status": "error", "message": "Tidak ada data untuk di-export"}), 400
    
    df = pd.DataFrame(data)
    cols = ['Judul', 'Sumber Nama Website', 'Deskripsi Artikel', 'Caption', 'Sumber', 'Tanggal']
    for col in cols:
        if col not in df.columns:
            df[col] = ''
            
    df = df[cols]
    df.rename(columns={'Sumber Nama Website': 'Sumber Media', 'Caption': 'Caption AI'}, inplace=True)
    
    output = io.BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='hasil_berita_dan_caption.csv'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)