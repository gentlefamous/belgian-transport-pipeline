{% macro source(source_name, table_name) %}
    {% set sources = {
        'raw_transport': {
            'departures': "read_parquet('../../data/processed/**/*.parquet', union_by_name=true)"
        }
    } %}
    {{ sources[source_name][table_name] }}
{% endmacro %}