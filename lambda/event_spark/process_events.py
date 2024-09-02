import argparse
import base64
import json
import os
from datetime import datetime

from pyspark.sql import SparkSession


CATALOG_NAME = "AwsDataCatalog"
DATABASE_NAME = os.environ["GLUE_DATABASE_NAME"]
WAREHOUSE_LOCATION = os.environ["WAREHOUSE_LOCATION"]
EVENTS_TABLE_NAME = "events"
EVENTS_TABLE_IDENTIFIER = f"{CATALOG_NAME}.{DATABASE_NAME}.{EVENTS_TABLE_NAME}"
EVENTS_BASE_DDL = f"""CREATE TABLE IF NOT EXISTS {EVENTS_TABLE_IDENTIFIER} (
    event_time timestamp NOT NULL,
    event_type string NOT NULL,
    user_id string NOT NULL,
    session_id string NOT NULL,
    client_event_time timestamp NOT NULL,
    server_event_time timestamp NOT NULL,
    ip_address string,
    host string,
    path string
) USING iceberg
PARTITIONED BY (days(event_time))
TBLPROPERTIES ('table_type'='ICEBERG', 'classification' = 'parquet')
;"""
IDENTIFIES_TABLE_NAME = "identifies"
IDENTIFIES_TABLE_IDENTIFIER = f"{CATALOG_NAME}.{DATABASE_NAME}.{IDENTIFIES_TABLE_NAME}"
IDENTIFIES_BASE_DDL = f"""CREATE TABLE IF NOT EXISTS {IDENTIFIES_TABLE_IDENTIFIER} (
    event_time timestamp NOT NULL,
    prev_user_id string NOT NULL,
    new_user_id string NOT NULL,
    session_id string NOT NULL,
    client_event_time timestamp NOT NULL,
    server_event_time timestamp NOT NULL,
    ip_address string,
    host string,
    path string
) USING iceberg
TBLPROPERTIES ('table_type'='ICEBERG', 'classification' = 'parquet')
;"""


def spark_script(records):
    # aws_region = os.environ["AWS_REGION"]
    aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
    aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
    # session_token = os.environ["AWS_SESSION_TOKEN"]

    spark = _setup_spark(aws_access_key_id, aws_secret_access_key)

    _create_table_if_not_exists(
        spark, DATABASE_NAME, EVENTS_TABLE_NAME, EVENTS_BASE_DDL
    )
    _create_table_if_not_exists(
        spark, DATABASE_NAME, IDENTIFIES_TABLE_NAME, IDENTIFIES_BASE_DDL
    )

    print(f"Records lenght: {len(records)}")

    _handle_events(spark, [r["data"] for r in records if r["type"] == "event"])
    _handle_identifies(spark, [r["data"] for r in records if r["type"] == "identify"])


def _setup_spark(aws_access_key_id, aws_secret_access_key):
    return (
        SparkSession.builder.appName("Spark-on-AWS-Lambda")
        .master("local[*]")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.memory", "1g")
        .config("spark.executor.memory", "1g")
        .config("spark.hadoop.fs.s3a.access.key", aws_access_key_id)
        .config("spark.hadoop.fs.s3a.secret.key", aws_secret_access_key)
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.TemporaryAWSCredentialsProvider",
        )
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
        .config(
            "spark.sql.catalog.AwsDataCatalog", "org.apache.iceberg.spark.SparkCatalog"
        )
        .config(
            "spark.sql.catalog.AwsDataCatalog.catalog-impl",
            "org.apache.iceberg.aws.glue.GlueCatalog",
        )
        .config("spark.sql.catalog.AwsDataCatalog.warehouse", WAREHOUSE_LOCATION)
        .config(
            "spark.hadoop.hive.metastore.client.factory.class",
            "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory",
        )
        .config("spark.sql.iceberg.handle-timestamp-without-timezone", "true")
        .getOrCreate()
    )


def _create_table_if_not_exists(spark, database_name, table_name, ddl):
    if not spark.catalog.tableExists(f"{database_name}.{table_name}"):
        print(f"Table {database_name}.{table_name} does not exist, creating")
        spark.sql(ddl)
    else:
        print(f"Table {database_name}.{table_name} exists")


def _handle_events(spark, events):
    table = spark.table(EVENTS_TABLE_IDENTIFIER)
    print(f"Events table schema: {table.schema}")

    event_columns = set()
    for event in events:
        event_columns.update(event.keys())

        event["server_event_time"] = datetime.fromisoformat(
            event["server_event_time"].replace("Z", "+00:00")
        )
        event["client_event_time"] = datetime.fromisoformat(
            event["client_event_time"].replace("Z", "+00:00")
        )
        event["event_time"] = event["server_event_time"]

    for column in event_columns:
        if column not in table.schema.names:
            print(f"Adding a new column {column} to table schema")
            spark.sql(
                f"ALTER TABLE {EVENTS_TABLE_IDENTIFIER} ADD COLUMN {column} string"
            )

    df = spark.createDataFrame(data=events, schema=table.schema)
    df.printSchema()
    df.writeTo(EVENTS_TABLE_IDENTIFIER).append()


def _handle_identifies(spark, identifies):
    table = spark.table(IDENTIFIES_TABLE_IDENTIFIER)
    print(f"Identifies table schema: {table.schema}")

    for identify in identifies:
        identify["server_event_time"] = datetime.fromisoformat(
            identify["server_event_time"].replace("Z", "+00:00")
        )
        identify["client_event_time"] = datetime.fromisoformat(
            identify["client_event_time"].replace("Z", "+00:00")
        )
        identify["event_time"] = identify["server_event_time"]

    df = spark.createDataFrame(data=identifies, schema=table.schema)
    df.printSchema()
    df.writeTo(IDENTIFIES_TABLE_IDENTIFIER).append()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-file", help="Kinesis events")
    args = parser.parse_args()

    with open(args.event_file) as f:
        json_obj = json.load(f)
    records = []
    for record in json_obj["Records"]:
        records.append(
            json.loads(base64.b64decode(record["kinesis"]["data"]).decode("utf-8"))
        )

    spark_script(records)
