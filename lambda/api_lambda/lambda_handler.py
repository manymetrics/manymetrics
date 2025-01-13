import os
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from functools import wraps
from typing import Any, Literal, TypedDict

import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)


KINESIS_STREAM_NAME = os.environ.get("KINESIS_STREAM_NAME")

kinesis_client = boto3.client("kinesis")


def log_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        logger.info(f"Response: {response}")
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


class BadRequestError(Exception):
    pass


class InternalServerError(Exception):
    pass


@log_response
def lambda_handler(lambda_event, context) -> dict[str, Any]:
    return _handle_event(lambda_event).to_lambda_response()


def _handle_event(lambda_event: dict[str, Any]) -> Response:
    logger.info(f"Received lambda_event: {json.dumps(lambda_event)}")

    if _is_cors_request(lambda_event):
        return Response(statusCode=200, headers=_get_cors_headers(lambda_event))

    response_headers = {
        "Content-Type": "application/json",
        **_get_cors_headers(lambda_event),
    }

    try:
        if lambda_event.get("httpMethod") != "POST":
            raise BadRequestError("Bad Request")

        handlers = {"/track": _track, "/identify": _identify}

        path = lambda_event.get("path")
        if not path or path not in handlers:
            raise BadRequestError("Bad Request")

        handlers[path](lambda_event)

    except BadRequestError as e:
        return Response(
            statusCode=400,
            headers=response_headers,
            body={"message": str(e)},
        )
    except InternalServerError as e:
        return Response(
            statusCode=500,
            headers=response_headers,
            body={"message": str(e)},
        )

    return Response(
        statusCode=200,
        headers=response_headers,
        body={"message": "Ok"},
    )


def _track(lambda_event: dict[str, Any]):
    event = _extract_and_enrich_event(lambda_event)

    _write_to_kinesis(
        {
            "type": "event",
            "data": event,
        },
        partition_key=event["user_id"],
    )


def _identify(lambda_event: dict[str, Any]):
    event = _extract_and_enrich_event(lambda_event)

    _write_to_kinesis(
        {
            "type": "identify",
            "data": event,
        },
        partition_key=event["prev_user_id"],
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

    origin = lambda_event["headers"].get("origin", "*")
    headers["Access-Control-Allow-Origin"] = origin
    return headers


def _extract_and_enrich_event(lambda_event: dict[str, Any]) -> dict[str, Any]:
    try:
        event = json.loads(lambda_event["body"])
    except json.JSONDecodeError:
        raise BadRequestError("Bad Request")

    if not isinstance(event, dict):
        raise BadRequestError("Bad Request")

    event["server_event_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    event["ip_address"] = lambda_event["requestContext"]["identity"]["sourceIp"]

    return event


class _KinesisEvent(TypedDict):
    type: Literal["event", "identify"]
    data: dict[str, Any]


def _write_to_kinesis(data: _KinesisEvent, partition_key: str):
    try:
        kinesis_client.put_record(
            StreamName=KINESIS_STREAM_NAME,
            Data=json.dumps(data),
            PartitionKey=partition_key,
        )
    except Exception:
        logger.exception("Kinesis error")
        raise InternalServerError("Kinesis error")
