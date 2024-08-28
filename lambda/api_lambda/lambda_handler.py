import os
import json
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime
from functools import wraps
from typing import Any

import boto3


KINESIS_STREAM_NAME = os.environ.get("KINESIS_STREAM_NAME")

kinesis_client = boto3.client("kinesis")


def log_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        print("Response: " + str(response))
        return response

    return wrapper


@dataclass(frozen=True, kw_only=True)
class Response:
    statusCode: int
    headers: dict[str, str]
    body: dict[str, Any] | None = None

    def to_lambda_response(self) -> dict[str, Any]:
        lambda_response = asdict(self)
        if self.body is not None:
            lambda_response["body"] = json.dumps(self.body)
        return lambda_response


@log_response
def lambda_handler(lambda_event, context) -> dict[str, Any]:
    return _handle_event(lambda_event).to_lambda_response()


def _handle_event(lambda_event: dict[str, Any]) -> Response:
    print("Received lambda_event: " + json.dumps(lambda_event))

    if _is_cors_request(lambda_event):
        return Response(statusCode=200, headers=_get_cors_headers(lambda_event))

    response_headers = {
        "Content-Type": "application/json",
        **_get_cors_headers(lambda_event),
    }

    if not _validate_lambda_event(lambda_event):
        return Response(
            statusCode=400,
            headers=response_headers,
            body={"message": "Bad Request"},
        )

    try:
        event = _extract_and_enrich_event(lambda_event)
    except json.JSONDecodeError:
        return Response(
            statusCode=400,
            headers=response_headers,
            body={"message": "Bad Request"},
        )

    try:
        response = kinesis_client.put_record(
            StreamName=KINESIS_STREAM_NAME,
            Data=json.dumps(event),
            PartitionKey="partition_key",
        )
        print("Response from Kinesis: " + json.dumps(response))
        return Response(
            statusCode=200,
            headers=response_headers,
            body={
                "message": "Ok",
            },
        )
    except Exception as e:
        traceback.print_exception(e)
        return Response(
            statusCode=500,
            headers=response_headers,
            body={
                "message": "Failed to send data to Kinesis stream",
                "error": str(e),
            },
        )


def _is_cors_request(lambda_event: dict[str, Any]) -> bool:
    return lambda_event.get("httpMethod") == "OPTIONS"


def _get_cors_headers(lambda_event: dict[str, Any]):
    headers = {
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
        "Access-Control-Allow-Credentials": True,
    }

    if "origin" in lambda_event["headers"]:
        origin = lambda_event["headers"]["origin"]
    else:
        origin = "*"

    headers["Access-Control-Allow-Origin"] = origin
    return headers


def _validate_lambda_event(lambda_event: dict[str, Any]) -> bool:
    if lambda_event.get("httpMethod") != "POST":
        return False

    if lambda_event.get("path") != "/track":
        return False

    return True


def _extract_and_enrich_event(lambda_event: dict[str, Any]) -> dict[str, Any]:
    event = json.loads(lambda_event["body"])

    event["server_event_time"] = (
        datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    )
    event["ip_address"] = lambda_event["requestContext"]["identity"]["sourceIp"]

    return event
