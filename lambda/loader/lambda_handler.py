from datetime import datetime
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NoSuchTableError
from pyiceberg.types import (
    StringType,
    TimestampType,
)
import pyarrow as pa
import os

DATABASE_NAME = os.environ["GLUE_DATABASE_NAME"]
EVENTS_TABLE_NAME = "events"
IDENTIFIES_TABLE_NAME = "identifies"
EVENTS_SCHEMA = {
    "event_time": TimestampType(),
    "event_type": StringType(),
    "user_id": StringType(),
    "session_id": StringType(),
    "client_event_time": TimestampType(),
    "server_event_time": TimestampType(),
    "ip_address": StringType(),
    "host": StringType(),
    "path": StringType(),
    "referrer": StringType(),
    "user_agent": StringType(),
}

IDENTIFIES_SCHEMA = {
    "event_time": TimestampType(),
    "prev_user_id": StringType(),
    "new_user_id": StringType(),
    "session_id": StringType(),
    "client_event_time": TimestampType(),
    "server_event_time": TimestampType(),
    "ip_address": StringType(),
    "host": StringType(),
    "path": StringType(),
    "user_agent": StringType(),
}


def lambda_handler(event: dict, context: dict) -> None:
    catalog = load_catalog(
        "glue",
        **{
            "client.access-key-id": os.environ["AWS_ACCESS_KEY_ID"],
            "client.secret-access-key": os.environ["AWS_SECRET_ACCESS_KEY"],
            "client.region": "eu-west-1",
        },
        type="glue",
    )

    _create_table_if_not_exists(catalog, DATABASE_NAME, EVENTS_TABLE_NAME, EVENTS_SCHEMA)
    _create_table_if_not_exists(catalog, DATABASE_NAME, IDENTIFIES_TABLE_NAME, IDENTIFIES_SCHEMA)

    # Get records from event
    records = event.get("Records", [])
    if not records:
        print("No records to process")
        return

    events_table = catalog.load_table(f"{DATABASE_NAME}.{EVENTS_TABLE_NAME}")
    events = [r["data"] for r in records if r["type"] == "event"]
    if events:
        _handle_events(events_table, events)

    identifies_table = catalog.load_table(f"{DATABASE_NAME}.{IDENTIFIES_TABLE_NAME}")
    identifies = [r["data"] for r in records if r["type"] == "identify"]
    if identifies:
        _handle_identifies(identifies_table, identifies)


def _create_table_if_not_exists(catalog, database_name: str, table_name: str, schema: dict) -> None:
    try:
        catalog.load_table(f"{database_name}.{table_name}")
        print(f"Table {database_name}.{table_name} exists")
    except NoSuchTableError:
        print(f"Table {database_name}.{table_name} does not exist, creating")
        catalog.create_table(
            identifier=f"{database_name}.{table_name}",
            schema=schema,
            properties={
                "format-version": "2",
            },
        )


def _handle_events(table, events: list[dict]) -> None:
    current_columns = set(field.name for field in table.schema().fields)

    print("len(events)", len(events))
    event_columns = set()
    for event in events:
        event_columns.update(event.keys())

        # Convert timestamps
        event["server_event_time"] = _convert_timestamp(event["server_event_time"])
        event["client_event_time"] = _convert_timestamp(event["client_event_time"])
        event["event_time"] = event["server_event_time"]

    # Add any new columns to schema
    new_columns = event_columns - current_columns
    if new_columns:
        updates = table.update_schema()
        for column in new_columns:
            print(f"Adding new column: {column}")
            updates.add_column(column, StringType())
        updates.commit()

    # Create arrow table and append
    df = pa.Table.from_pylist(events, schema=table.schema().as_arrow())
    table.append(df)


def _handle_identifies(table, identifies: list[dict]) -> None:
    print("len(identifies)", len(identifies))
    for identify in identifies:
        identify["server_event_time"] = _convert_timestamp(identify["server_event_time"])
        identify["client_event_time"] = _convert_timestamp(identify["client_event_time"])
        identify["event_time"] = identify["server_event_time"]

    df = pa.Table.from_pylist(identifies, schema=table.schema().as_arrow())
    table.append(df)


def _convert_timestamp(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
