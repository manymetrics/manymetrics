import sys
import os
import subprocess
import logging
import json

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def spark_submit(event: dict) -> None:
    code_dir = os.path.dirname(os.path.realpath(__file__))
    logger.info("Submitting the Spark script")
    subprocess.run(
        ["spark-submit", f"{code_dir}/process_events.py", "--event", json.dumps(event)],
        check=True,
        env=os.environ,
    )


def lambda_handler(event, context):
    spark_submit(event)
