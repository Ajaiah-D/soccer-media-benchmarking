select
    channel_name,
    subscriber_count,
    view_count,
    video_count,
    round(avg_views_per_video, 0)      as avg_views_per_video,
    round(views_per_subscriber, 4)     as views_per_subscriber,
    rank() over (
        order by views_per_subscriber desc
    )                                  as performance_rank,
    ingested_at
from {{ ref('int_channel_metrics') }}
