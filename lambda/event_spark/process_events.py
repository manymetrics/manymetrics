import argparse
import base64
from datetime import datetime
import json
import os

from pyspark.sql import SparkSession


BASE_DDL = """CREATE TABLE IF NOT EXISTS {table_identifier} (
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
LOCATION '{target_path}'
TBLPROPERTIES ('table_type'='ICEBERG', 'classification' = 'parquet')
;"""


def spark_script(records):
    # aws_region = os.environ["AWS_REGION"]
    aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
    aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
    # session_token = os.environ["AWS_SESSION_TOKEN"]

    catalog_name = "AwsDataCatalog"
    database_name = os.environ["GLUE_DATABASE_NAME"]
    table_name = "events"
    target_path = os.environ["EVENTS_S3_URI"]
    table_identifier = f"{catalog_name}.{database_name}.{table_name}"

    spark = _setup_spark(aws_access_key_id, aws_secret_access_key, target_path)

    if not spark.catalog.tableExists(f"{database_name}.{table_name}"):
        print(f"Table {table_identifier} does not exist, creating")
        spark.sql(
            BASE_DDL.format(table_identifier=table_identifier, target_path=target_path)
        )
    else:
        print(f"Table {table_identifier} exists")

    table = spark.table(table_identifier)
    print(f"Table schema: {table.schema}")

    print(f"Records: {records}")

    events = []
    event_columns = set()
    for event in records:
        event_columns.update(event.keys())

        event["server_event_time"] = datetime.fromisoformat(
            event["server_event_time"].replace("Z", "+00:00")
        )
        event["client_event_time"] = datetime.fromisoformat(
            event["client_event_time"].replace("Z", "+00:00")
        )
        event["event_time"] = event["server_event_time"]
        events.append(event)

    for column in event_columns:
        if column not in table.schema.names:
            print(f"Adding column {column} to table schema")
            spark.sql(f"ALTER TABLE {table_identifier} ADD COLUMN {column} string")

    df = spark.createDataFrame(data=events, schema=table.schema)
    df.printSchema()
    df.writeTo(table_identifier).append()


def _setup_spark(aws_access_key_id, aws_secret_access_key, warehouse_location):
    return (
        SparkSession.builder.appName("Spark-on-AWS-Lambda")
        .master("local[*]")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.memory", "5g")
        .config("spark.executor.memory", "5g")
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
        .config("spark.sql.catalog.AwsDataCatalog.warehouse", warehouse_location)
        .config(
            "spark.hadoop.hive.metastore.client.factory.class",
            "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory",
        )
        .config("spark.sql.iceberg.handle-timestamp-without-timezone", "true")
        .getOrCreate()
    )


def decode_base64(encoded_str):
    return base64.b64decode(encoded_str).decode("utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="Kinesis events")
    args = parser.parse_args()

    json_obj = json.loads(args.event)
    records = []
    for record in json_obj["Records"]:
        records.append(
            json.loads(base64.b64decode(record["kinesis"]["data"]).decode("utf-8"))
        )

    spark_script(records)
