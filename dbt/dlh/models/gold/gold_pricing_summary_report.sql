{{ config(materialized="table", database="dlh-gold", schema="tpch") }}

/*
1 Q1 - Pricing Summary Report Query
This query reports the amount of business that was billed, shipped, and returned. 
Full description:https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-h_v3.0.1.pdf (Page 29)
*/
with
    orders_items as (select * from {{ ref("gold_fct_orders_items") }}),
    max_ship_date as (
        select max(ship_date) as highest_ship_date
        from orders_items
    )
select
    f.return_status_code,
    f.order_line_status_code,
    sum(f.quantity) as quantity,
    sum(f.gross_item_sales_amount) as gross_item_sales_amount,
    sum(f.discounted_item_sales_amount) as discounted_item_sales_amount,
    sum(f.net_item_sales_amount) as net_item_sales_amount,

    avg(f.quantity) as avg_quantity,
    avg(f.base_price) as avg_base_price,
    avg(f.discount_percentage) as avg_discount_percentage,

    sum(f.order_item_count) as order_item_count

from orders_items f
cross join max_ship_date d
where f.ship_date <= date_add('day', -90, d.highest_ship_date)
group by 1, 2
