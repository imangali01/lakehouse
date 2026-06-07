{% snapshot orders_snapshot %}
    {{
        config(
            target_database="dlh-bronze",
            target_schema="snapshot",
            unique_key="orderkey",
            strategy="timestamp",
            updated_at="orderdate",
        )
    }}

    select *
    from {{ source("tpch_raw", "orders") }}

{% endsnapshot %}
