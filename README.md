# MediaScrapper

A Python-based news scraping tool that collects and aggregates news articles from thousands of official media sources via Google News RSS. No AI API keys required — purely RSS-based scraping with built-in keyword analysis.

## Features

- **Pure RSS Scraping** — Fetches news from Google News RSS without any API key or usage limits
- **Flexible Search** — Search by topic, location, or both
- **Time Range Filtering** — Filter results by 24 hours, 7 days, 30 days, or all time
- **Keyword Analysis** — Automatically identifies the most frequently mentioned keywords across all collected articles
- **Structured JSON Output** — Exports results to a clean, well-formatted JSON file with metadata
- **Auto-Organized Storage** — Output files are saved in date-based folders (e.g., `17.07/`) with descriptive filenames

## Requirements

- **Python 3.10+**
- **Jupyter Notebook** (to run `engine.ipynb`)

### Python Dependencies

| Package      | Description                              |
|--------------|------------------------------------------|
| `feedparser` | Parses Google News RSS/Atom feeds        |
| `requests`   | Makes HTTP requests to the RSS endpoint  |

> Standard library modules used: `os`, `re`, `urllib.parse`, `json`, `collections`, `datetime`

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/MediaScrapper.git
   cd MediaScrapper
   ```

2. **Install dependencies**

   ```bash
   pip install feedparser requests
   ```

3. **Open the notebook**

   ```bash
   jupyter notebook engine.ipynb
   ```

## Usage

1. Open [`engine.ipynb`](engine.ipynb) in Jupyter Notebook
2. Run all cells. The interactive prompt will ask for:

   | Prompt | Description | Example |
   |--------|-------------|---------|
   | **Topik Berita** | The news topic to search for | `Kebakaran`, `Korupsi`, `Sepak Bola` |
   | **Lokasi** | Geographic focus of the news | `Bangkok`, `Indonesia`, `Seluruh dunia` |
   | **Rentang Waktu** | `1` = 24h, `2` = 7 days, `3` = 30 days, `4` = all time | `2` |
   | **Jumlah Maksimal** | Maximum number of articles to collect | `15` |

3. Results are printed to the console and exported to a JSON file automatically

### Output Structure

Results are saved in a date-based folder with the following naming convention:

```
DD.MM/scrape_{Topic}_{Location}_{YYYYMMDD}.json
```

**Example:** `17.07/scrape_Sepak_Bola_Seluruh_dunia_20260717.json`

The JSON file contains:

```json
{
    "metadata": {
        "total_berita": 15,
        "waktu_ekstraksi": "2026-07-17 13:20:36"
    },
    "berita": [
        {
            "source": "CNN Indonesia",
            "title": "Article headline here",
            "link": "https://news.google.com/rss/articles/...",
            "published": "Mon, 13 Jul 2026 03:44:42 GMT"
        }
    ],
    "kata_kunci_terpopuler": [
        {
            "peringkat": 1,
            "kata_kunci": "Keyword",
            "jumlah_kemunculan": 5
        }
    ]
}
```

## Project Structure

```
MediaScrapper/
├── engine.ipynb                                    # Main notebook with scraper logic
├── README.md                                       # Project documentation
├── .gitattributes                                  # Git configuration
├── scrape_Chat_GPT_Amerika_20260717.xlsx           # Sample output (Excel)
├── scrape_Korupsi_indonesia_20260717.xlsx           # Sample output (Excel)
└── 17.07/                                          # Date-based output folder
    ├── scrape_Kebakaran_bangkok_20260717.json       # Scraped news data
    ├── scrape_Kereta_api_Indonesia_20260717.json     # Scraped news data
    └── scrape_Sepak_Bola_Seluruh_dunia_20260717.json # Scraped news data
```

## How It Works

1. **Query Construction** — Combines the user-provided topic and location into a search query, appending a Google News time filter (`when:1d`, `when:7d`, `when:30d`) if applicable
2. **RSS Fetching** — Sends an HTTP GET request to `https://news.google.com/rss/search` with the encoded query
3. **Feed Parsing** — Uses `feedparser` to parse the XML response and extract article title, source, link, and publication date
4. **Keyword Extraction** — Tokenizes all article titles, filters out Indonesian stop words, and counts word frequencies using `collections.Counter`
5. **JSON Export** — Serializes the collected data and keyword analysis into a structured JSON file

## License

This project is open-source and available for personal and educational use.
