import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.cloud import bigquery

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET")
TABLE_ID = "raw_channels"

# Keyed by YouTube handle (without @), value is a friendly label for logging
CHANNEL_HANDLES = {
    "brfootball":       "B/R Football",
    "cbssportsgolazo":  "CBS Sports Golazo",
    "theathleticfc":    "The Athletic FC",
    "Tifo":     "Tifo Football",
    "Copa90":           "Copa90",
}

SCHEMA = [
    bigquery.SchemaField("ingested_at", "TIMESTAMP"),
    bigquery.SchemaField("channel_id", "STRING"),
    bigquery.SchemaField("channel_name", "STRING"),
    bigquery.SchemaField("subscriber_count", "INTEGER"),
    bigquery.SchemaField("view_count", "INTEGER"),
    bigquery.SchemaField("video_count", "INTEGER"),
]


def resolve_handle(youtube, handle: str) -> dict | None:
    """Return the channel item for a given handle, or None if not found."""
    response = youtube.channels().list(
        part="snippet,statistics",
        forHandle=handle,
    ).execute()
    items = response.get("items", [])
    return items[0] if items else None


def fetch_all_channels(api_key: str, handles: dict) -> list[dict]:
    youtube = build("youtube", "v3", developerKey=api_key)
    rows = []
    ingested_at = datetime.now(timezone.utc).isoformat()

    for handle, label in handles.items():
        item = resolve_handle(youtube, handle)
        if item is None:
            print(f"  WARNING: could not resolve @{handle} ({label}) — skipping")
            continue

        stats = item["statistics"]
        actual_name = item["snippet"]["title"]
        rows.append({
            "ingested_at":      ingested_at,
            "channel_id":       item["id"],
            "channel_name":     actual_name,
            "subscriber_count": int(stats.get("subscriberCount", 0)),
            "view_count":       int(stats.get("viewCount", 0)),
            "video_count":      int(stats.get("videoCount", 0)),
        })
        print(f"  {actual_name}: {int(stats.get('subscriberCount', 0)):,} subscribers")

    return rows


def load_to_bigquery(rows: list[dict]) -> None:
    client = bigquery.Client(project=GCP_PROJECT_ID)
    dataset_ref = client.dataset(BIGQUERY_DATASET)

    try:
        client.get_dataset(dataset_ref)
    except Exception:
        client.create_dataset(dataset_ref)
        print(f"Created dataset {BIGQUERY_DATASET}")

    table_ref = dataset_ref.table(TABLE_ID)

    try:
        client.get_table(table_ref)
    except Exception:
        table = bigquery.Table(table_ref, schema=SCHEMA)
        client.create_table(table)
        print(f"Created table {TABLE_ID}")

    errors = client.insert_rows_json(table_ref, rows)
    if errors:
        raise RuntimeError(f"BigQuery insert errors: {errors}")

    print(f"Inserted {len(rows)} rows into {BIGQUERY_DATASET}.{TABLE_ID}")


def main():
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY not set in .env")
    if not GCP_PROJECT_ID or not BIGQUERY_DATASET:
        raise ValueError("GCP_PROJECT_ID and BIGQUERY_DATASET must be set in .env")

    print(f"Fetching stats for {len(CHANNEL_HANDLES)} channels...\n")
    rows = fetch_all_channels(YOUTUBE_API_KEY, CHANNEL_HANDLES)

    if not rows:
        raise RuntimeError("No channels resolved — check handles in CHANNEL_HANDLES")

    print()
    load_to_bigquery(rows)


if __name__ == "__main__":
    main()
