"""Functions for interacting with Google BigQuery."""

import logging

from google.api_core.exceptions import BadRequest
from google.cloud import bigquery


def run_query(query):
    # Delete all items from yesterday import
    bq = bigquery.Client()
    try:
        results = bq.query(query).to_dataframe()
        logging.info("📝 Successfully executed query")
    except BadRequest as e:
        logging.info("⛔️ Unsuccessful query execution: %s", e)
        return False, e.message
    else:
        return True, results


def bq_schema_to_sql(schema_field: bigquery.SchemaField, indent: int = 2) -> str:
    """Convert a BigQuery SchemaField to its SQL representation."""
    field_name = schema_field.name
    field_type = schema_field.field_type
    mode = schema_field.mode

    space = " " * indent

    # Handle nested records by recursively calling the function.
    if field_type == "RECORD":
        nested_fields = ",\n".join(
            [
                f"{space}{bq_schema_to_sql(f, indent=indent + 2)}"
                for f in schema_field.fields
            ],
        )
        field_str = f"STRUCT<\n{nested_fields}\n{space}>"
    else:
        field_str = field_type

    # Handle field modes
    if mode == "NULLABLE":
        field_str = f"{field_name} {field_str}"
    elif mode == "REPEATED":
        field_str = f"{field_name} ARRAY<{field_str}>"
    elif mode == "REQUIRED":
        field_str = f"{field_name} {field_str} NOT NULL"

    return field_str


def generate_create_table_sql(table_id: str) -> str:
    """Generate a SQL CREATE TABLE query from a BigQuery table."""
    client = bigquery.Client()
    table = client.get_table(table_id)
    schema = table.schema
    table_id = table.table_id
    fields_str = ",\n".join([f"  {bq_schema_to_sql(field)}" for field in schema])

    return f"CREATE TABLE {table} (\n{fields_str}\n);"
