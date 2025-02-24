from datetime import datetime
from pyiceberg.catalog import load_catalog
from pyiceberg.types import (
    StringType,
)
import pyarrow as pa
import os


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

    # Get records from event
    records = event.get("Records", [])
    if not records:
        print("No records to process")
        return

    events_table = catalog.load_table("manymetrics_site2.events")
    events = [r["data"] for r in records if r["type"] == "event"]
    if events:
        _handle_events(events_table, events)

    identifies_table = catalog.load_table("manymetrics_site2.identifies")
    identifies = [r["data"] for r in records if r["type"] == "identify"]
    if identifies:
        _handle_identifies(identifies_table, identifies)


def _handle_events(table, events):
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


def _handle_identifies(table, identifies):
    print("len(identifies)", len(identifies))
    for identify in identifies:
        identify["server_event_time"] = _convert_timestamp(identify["server_event_time"])
        identify["client_event_time"] = _convert_timestamp(identify["client_event_time"])
        identify["event_time"] = identify["server_event_time"]

    df = pa.Table.from_pylist(identifies, schema=table.schema().as_arrow())
    table.append(df)


def _convert_timestamp(timestamp):
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


if __name__ == "__main__":
    # Test event
    test_event = {
        "Records": [
            {
                "type": "event",
                "data": {
                    "event_time": "2024-01-01T12:00:00Z",
                    "event_type": "test_event_pyiceberg",
                    "user_id": "123",
                    "session_id": "456",
                    "client_event_time": "2024-01-01T12:00:00Z",
                    "server_event_time": "2024-01-01T12:00:00Z",
                    "ip_address": "192.168.1.1",
                    "host": "example.com",
                    "path": "/",
                    "referrer": "https://example.com",
                    "user_agent": "Mozilla/5.0",
                },
            }
        ]
    }
    lambda_handler(test_event, {})
