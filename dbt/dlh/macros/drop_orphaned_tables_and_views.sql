{%- macro drop_orphaned_tables_and_views(dry_run="true") -%}
    {%- if not execute -%}
        {{ return("") }}
    {%- endif -%}

    {%- set current_model_locations = {} -%}
    {%- for node in graph.nodes.values() | selectattr("resource_type", "in", ["model", "seed", "snapshot"]) -%}
        {%- set database_name = node.database -%}
        {%- set schema_name = node.schema -%}
        {%- set relation_name = node.alias if node.alias else node.name -%}

        {%- if database_name not in current_model_locations -%}
            {% do current_model_locations.update({database_name: {}}) -%}
        {%- endif -%}
        {%- if schema_name not in current_model_locations[database_name] -%}
            {% do current_model_locations[database_name].update({schema_name: []}) -%}
        {%- endif -%}
        {%- do current_model_locations[database_name][schema_name].append(relation_name) -%}
    {%- endfor -%}

    {%- set drop_commands = [] -%}

    {%- for database_name, schemas in current_model_locations.items() -%}
        {%- for schema_name, relations in schemas.items() -%}
            {%- set cleanup_query -%}
                select
                    case when table_type = 'BASE TABLE' then 'TABLE' else 'VIEW' end as relation_type,
                    table_catalog,
                    table_schema,
                    table_name
                from {{ adapter.quote(database_name) }}.information_schema.tables
                where lower(table_schema) = lower('{{ schema_name }}')
                  and lower(table_name) not in (
                    {%- for relation_name in relations -%}
                        lower('{{ relation_name }}'){% if not loop.last %}, {% endif %}
                    {%- endfor -%}
                  )
            {%- endset -%}

            {%- set results = run_query(cleanup_query) -%}
            {%- if results is not none and results.rows -%}
                {%- for row in results.rows -%}
                    {%- set relation_type = row[0] -%}
                    {%- set table_catalog = row[1] -%}
                    {%- set table_schema = row[2] -%}
                    {%- set table_name = row[3] -%}
                    {%- do drop_commands.append(
                        "DROP " ~ relation_type ~ " IF EXISTS "
                        ~ adapter.quote(table_catalog) ~ "."
                        ~ adapter.quote(table_schema) ~ "."
                        ~ adapter.quote(table_name) ~ ";"
                    ) -%}
                {%- endfor -%}
            {%- endif -%}
        {%- endfor -%}
    {%- endfor -%}

    {%- if drop_commands -%}
        {%- for drop_command in drop_commands -%}
            {%- do log(drop_command, True) -%}
            {%- if dry_run | upper == "FALSE" -%}
                {%- do run_query(drop_command) -%}
                {%- do log("Executed", True) -%}
            {%- endif -%}
        {%- endfor -%}
    {%- else -%}
        {%- do log("No relations to clean", True) -%}
    {%- endif -%}
{%- endmacro -%}
