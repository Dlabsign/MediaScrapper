from google import genai

# Masukkan API Key baru kamu di sini
client = genai.Client(api_key="AQ.Ab8RN6IJ26P7-uz-0lcdwpXLe0jT-2ddaFZXwA60tvDWVNvtwQ")

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='Halo Gemini, apakah kunci API ini sudah aktif?',
)

print(response.text)