

  create or replace view `soccer-benchmarking`.`soccer_media`.`stg_channels`
  OPTIONS()
  as select
    channel_id,
    channel_name,
    cast(subscriber_count as int64) as subscriber_count,
    cast(view_count as int64)       as view_count,
    cast(video_count as int64)      as video_count,
    ingested_at
from `soccer-benchmarking`.`soccer_media`.`raw_channels`
qualify row_number() over (
    partition by channel_id
    order by ingested_at desc
) = 1;

