{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- if custom_schema_name is not none -%}
        {# Если у модели или папки в dbt_project.yml явно задана схема, используем ТОЛЬКО её #}
        {{ custom_schema_name | trim }}
    {%- else -%}
        {# Если схема не задана, используем дефолтную из profiles.yml #}
        {{ target.schema }}
    {%- endif -%}

{%- endmacro %}