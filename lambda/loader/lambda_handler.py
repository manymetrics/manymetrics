import base64
from datetime import datetime
import json
import logging
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NoSuchTableError
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.transforms import DayTransform, IdentityTransform
from pyiceberg.table.sorting import SortOrder, SortField
from pyiceberg.types import (
    StringType,
    TimestampType,
    NestedField,
)
from pyiceberg.schema import Schema
import pyarrow as pa
import os

DATABASE_NAME = os.environ["GLUE_DATABASE_NAME"]
WAREHOUSE_LOCATION = os.environ["WAREHOUSE_LOCATION"]
DEPLOYMENT_TIMESTAMP = os.environ.get("DEPLOYMENT_TIMESTAMP")
EVENTS_TABLE_NAME = "events"
IDENTIFIES_TABLE_NAME = "identifies"
PARTITION_SPEC = PartitionSpec(
    PartitionField(name="day", field_id=10001, transform=DayTransform(), source_id=1),
)
EVENTS_SCHEMA = Schema(
    NestedField(field_id=1, name="event_time", field_type=TimestampType()),
    NestedField(field_id=2, name="event_type", field_type=StringType()),
    NestedField(field_id=3, name="user_id", field_type=StringType()),
    NestedField(field_id=4, name="session_id", field_type=StringType()),
    NestedField(field_id=5, name="client_event_time", field_type=TimestampType()),
    NestedField(field_id=6, name="server_event_time", field_type=TimestampType()),
    NestedField(field_id=7, name="ip_address", field_type=StringType()),
    NestedField(field_id=8, name="host", field_type=StringType()),
    NestedField(field_id=9, name="path", field_type=StringType()),
    NestedField(field_id=10, name="referrer", field_type=StringType()),
    NestedField(field_id=11, name="user_agent", field_type=StringType()),
)
IDENTIFIES_SCHEMA = Schema(
    NestedField(field_id=1, name="event_time", field_type=TimestampType()),
    NestedField(field_id=2, name="prev_user_id", field_type=StringType()),
    NestedField(field_id=3, name="new_user_id", field_type=StringType()),
    NestedField(field_id=4, name="session_id", field_type=StringType()),
    NestedField(field_id=5, name="client_event_time", field_type=TimestampType()),
    NestedField(field_id=6, name="server_event_time", field_type=TimestampType()),
    NestedField(field_id=7, name="ip_address", field_type=StringType()),
    NestedField(field_id=8, name="host", field_type=StringType()),
    NestedField(field_id=9, name="path", field_type=StringType()),
    NestedField(field_id=10, name="referrer", field_type=StringType()),
    NestedField(field_id=11, name="user_agent", field_type=StringType()),
)
SORT_ORDER = SortOrder(SortField(source_id=1, transform=IdentityTransform()))

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict, context: dict) -> None:
    catalog = load_catalog(
        "glue",
        **{
            # "client.access-key-id": os.environ["AWS_ACCESS_KEY_ID"],
            # "client.secret-access-key": os.environ["AWS_SECRET_ACCESS_KEY"],
            "client.region": "eu-west-1",
        },
        type="glue",
    )

    _create_table_if_not_exists(
        catalog, DATABASE_NAME, EVENTS_TABLE_NAME, EVENTS_SCHEMA
    )
    _create_table_if_not_exists(
        catalog, DATABASE_NAME, IDENTIFIES_TABLE_NAME, IDENTIFIES_SCHEMA
    )

    records = [_decode_record(record) for record in event.get("Records", [])]
    logger.info(f"Processing {records} records")

    if not records:
        logger.info("No records to process")
        return

    events_table = catalog.load_table(f"{DATABASE_NAME}.{EVENTS_TABLE_NAME}")
    events = [r["data"] for r in records if r["type"] == "event"]
    if events:
        _handle_events(events_table, events)

    identifies_table = catalog.load_table(f"{DATABASE_NAME}.{IDENTIFIES_TABLE_NAME}")
    identifies = [r["data"] for r in records if r["type"] == "identify"]
    if identifies:
        _handle_identifies(identifies_table, identifies)

    if len(events) + len(identifies) != len(records):
        unknown_records_len = len(records) - (len(events) + len(identifies))
        logger.warn(f"Unknown records: {unknown_records_len}")


def _decode_record(record: dict) -> dict:
    return json.loads(base64.b64decode(record["kinesis"]["data"]).decode("utf-8"))


def _create_table_if_not_exists(
    catalog, database_name: str, table_name: str, schema: dict
) -> None:
    try:
        catalog.load_table(f"{database_name}.{table_name}")
        logger.info(f"Table {database_name}.{table_name} exists")
    except NoSuchTableError:
        logger.info(f"Table {database_name}.{table_name} does not exist, creating")
        catalog.create_table(
            identifier=f"{database_name}.{table_name}",
            location=WAREHOUSE_LOCATION,
            schema=schema,
            partition_spec=PARTITION_SPEC,
            sort_order=SORT_ORDER,
            properties={
                "format-version": "2",
            },
        )


def _handle_events(table, events: list[dict]) -> None:
    current_columns = set(field.name for field in table.schema().fields)

    logger.info(f"Handling {len(events)} events")
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
            logger.info(f"Adding new column: {column}")
            updates.add_column(column, StringType())
        updates.commit()

    # Create arrow table and append
    df = pa.Table.from_pylist(events, schema=table.schema().as_arrow())
    table.append(df)


def _handle_identifies(table, identifies: list[dict]) -> None:
    logger.info(f"Handling {len(identifies)} identifies")
    for identify in identifies:
        identify["server_event_time"] = _convert_timestamp(
            identify["server_event_time"]
        )
        identify["client_event_time"] = _convert_timestamp(
            identify["client_event_time"]
        )
        identify["event_time"] = identify["server_event_time"]

    df = pa.Table.from_pylist(identifies, schema=table.schema().as_arrow())
    table.append(df)


def _convert_timestamp(timestamp: str) -> datetime:
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
