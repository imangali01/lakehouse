{% macro dateadd(datepart, interval, from_date_or_timestamp) %}
    {{ adapter.dispatch("dateadd", datepart, interval, from_date_or_timestamp) }}
{% endmacro %}

{% macro trino__dateadd(datepart, interval, from_date_or_timestamp) %}
    date_add(
        {{ datepart }},
        {{ interval }},
        {{ from_date_or_timestamp }}
    )
{% endmacro %}

{% macro default__dateadd(datepart, interval, from_date_or_timestamp) %}
    dateadd({{ datepart }}, {{ interval }}, {{ from_date_or_timestamp }})
{% endmacro %}
