select
    channel_id,
    channel_name,
    subscriber_count,
    view_count,
    video_count,
    ingested_at,
    safe_divide(view_count, video_count)      as avg_views_per_video,
    safe_divide(view_count, subscriber_count) as views_per_subscriber
from `soccer-benchmarking`.`soccer_media`.`stg_channels`