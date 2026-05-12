# soccer-media-benchmarking

Pulls channel stats from five soccer YouTube channels via the YouTube Data API, loads them into BigQuery, transforms them with dbt, and surfaces the results in a Streamlit dashboard. The core metric is views per subscriber: a way to compare channels on engagement rather than raw size.

## Stack

| Layer | Tool |
|---|---|
| Ingestion | Python + YouTube Data API v3 |
| Warehouse | Google BigQuery |
| Transformation | dbt |
| Dashboard | Streamlit |

## Channels

- B/R Football
- CBS Sports Golazo
- The Athletic FC
- Tifo Football
- Copa90

## Project structure

```
soccer-media-benchmarking/
├── ingestion/fetch_channels.py   # pulls from YouTube API, loads to BigQuery
├── dbt/
│   └── models/
│       ├── staging/              # type casting, deduplication
│       ├── intermediate/         # derived metrics
│       └── marts/                # final tables the dashboard reads
├── dashboard/app.py              # Streamlit app
├── .env.example                  # required environment variables
└── requirements.txt
```

## Setup

**1. Create a virtual environment and install dependencies**
```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows
pip install -r requirements.txt
```

**2. Configure credentials**

Copy `.env.example` to `.env` and fill in:
```
YOUTUBE_API_KEY=...
GCP_PROJECT_ID=...
BIGQUERY_DATASET=...
GOOGLE_APPLICATION_CREDENTIALS=gcp-key.json
```

Place your GCP service account JSON key in the project root as `gcp-key.json`. Both `.env` and `*.json` are gitignored.

**3. Run the pipeline**
```bash
# Fetch from YouTube and load to BigQuery
python ingestion/fetch_channels.py

# Transform with dbt (from project root)
set -a && source .env && set +a
dbt run --project-dir dbt --profiles-dir dbt

# Launch the dashboard
streamlit run dashboard/app.py
```

## Key metric

Views per subscriber divides total lifetime views by subscriber count. A smaller channel that outranks a larger one here has an audience that watches more, which is a better signal of content quality than subscriber count alone.
