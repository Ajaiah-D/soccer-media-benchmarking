import os
import streamlit as st
from dotenv import load_dotenv
from google.cloud import bigquery
import pandas as pd
import plotly.express as px

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET")


def fmt(n):
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(int(n))


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    client = bigquery.Client(project=GCP_PROJECT_ID)
    query = f"""
        SELECT
            channel_name, subscriber_count, view_count,
            video_count, avg_views_per_video, views_per_subscriber,
            performance_rank, ingested_at
        FROM `{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.channel_performance`
        ORDER BY performance_rank
    """
    return client.query(query).to_dataframe()


st.set_page_config(page_title="Soccer Media Benchmarking", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    h1 { font-size: 1.8rem !important; font-weight: 700; }
    h2, h3 { font-size: 1.1rem !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.title("Soccer Media Benchmarking")
st.caption("Five soccer YouTube channels ranked by views per subscriber, a normalized measure of audience engagement.")

df = load_data()

st.divider()

c1, c2, c3 = st.columns(3)
c1.metric("Channels tracked", len(df))
c2.metric("Top performer", df.iloc[0]["channel_name"])
c3.metric("Snapshot date", str(df["ingested_at"].max())[:10])

st.divider()

st.subheader("Views per subscriber")
st.caption("Total lifetime views divided by subscriber count. Higher means the audience watches more.")

chart_df = df.sort_values("views_per_subscriber", ascending=True)

fig = px.bar(
    chart_df,
    x="views_per_subscriber",
    y="channel_name",
    orientation="h",
    text=chart_df["views_per_subscriber"].apply(lambda x: f"{x:.1f}"),
    color="views_per_subscriber",
    color_continuous_scale="Blues",
)

fig.update_layout(
    coloraxis_showscale=False,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    height=280,
    margin=dict(l=0, r=40, t=10, b=10),
    xaxis=dict(visible=False, showgrid=False),
    yaxis=dict(showgrid=False, title=""),
    font=dict(size=13),
)
fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Full breakdown")

display = df[[
    "performance_rank", "channel_name", "subscriber_count",
    "view_count", "video_count", "avg_views_per_video", "views_per_subscriber"
]].copy()

display["subscriber_count"]    = display["subscriber_count"].apply(fmt)
display["view_count"]          = display["view_count"].apply(fmt)
display["video_count"]         = display["video_count"].apply(fmt)
display["avg_views_per_video"] = display["avg_views_per_video"].apply(fmt)
display["views_per_subscriber"]= display["views_per_subscriber"].round(2)

display.columns = ["Rank", "Channel", "Subscribers", "Total Views", "Videos", "Avg Views/Video", "Views/Sub"]

st.dataframe(display, use_container_width=True, hide_index=True)
