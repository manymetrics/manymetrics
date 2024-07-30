import sys
import os
import subprocess
import logging
import json
import tempfile

DEPLOYMENT_TIMESTAMP = os.environ.get("DEPLOYMENT_TIMESTAMP", "unknown")

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def spark_submit(event: dict) -> None:
    code_dir = os.path.dirname(os.path.realpath(__file__))
    logger.info(
        f"Submitting the Spark script (deployment timestamp: {DEPLOYMENT_TIMESTAMP})"
    )

    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump(event, temp_file)

        subprocess.run(
            [
                "spark-submit",
                f"{code_dir}/process_events.py",
                "--event-file",
                temp_file.name,
            ],
            check=True,
            env=os.environ,
        )
    finally:
        if temp_file is not None:
            os.unlink(temp_file.name)


def lambda_handler(event, context):
    spark_submit(event)
