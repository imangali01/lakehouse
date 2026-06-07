{{ config(materialized="table", database="dlh-bronze", schema="tpch") }}
select
    nationkey as nation_key,
    name as nation_name,
    regionkey as region_key,
    comment as nation_comment
from {{ source("tpch_raw", "nation") }}
