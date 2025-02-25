import json
from unittest.mock import patch

import pytest

from lambda_handler import (
    lambda_handler,
    Response,
)


@pytest.fixture(autouse=True)
def set_KINESIS_STREAM_NAME():
    with patch("lambda_handler.KINESIS_STREAM_NAME", "test-stream"):
        yield


@pytest.fixture
def mock_kinesis():
    with patch("lambda_handler.kinesis_client") as mock:
        yield mock


@pytest.fixture
def sample_event():
    return {
        "event_type": "Pageview",
        "user_id": "qm0u3viu8",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "session_id": "w11gyv8xi",
        "client_event_time": "2025-01-13T11:25:50.052Z",
        "path": "/",
        "host": "127.0.0.1",
        "referrer": "",
    }


@pytest.fixture
def lambda_event_factory():
    def create_event(
        path: str,
        http_method="POST",
        body={},
        origin="http://localhost:3000",
    ):
        return {
            "httpMethod": http_method,
            "path": path,
            "body": json.dumps(body),
            "headers": {"origin": origin},
            "requestContext": {
                "identity": {
                    "sourceIp": "127.0.0.1",
                }
            },
        }

    return create_event


def test_cors_preflight(lambda_event_factory):
    event = lambda_event_factory(path="/track", http_method="OPTIONS")
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    assert response["headers"]["Access-Control-Allow-Origin"] == "http://localhost:3000"
    assert response["headers"]["Access-Control-Allow-Methods"] == "POST,OPTIONS"


def test_invalid_http_method(lambda_event_factory):
    event = lambda_event_factory(path="/track", http_method="GET")
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["message"] == "Bad Request"


def test_invalid_path(lambda_event_factory):
    event = lambda_event_factory(path="/invalid")
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["message"] == "Bad Request"


def test_track_event_success(lambda_event_factory, sample_event, mock_kinesis):
    event = lambda_event_factory(path="/track", body=sample_event)
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    assert json.loads(response["body"])["message"] == "Ok"

    mock_kinesis.put_record.assert_called_once()
    kwargs = mock_kinesis.put_record.call_args.kwargs

    assert kwargs["StreamName"] == "test-stream"
    kinesis_data = json.loads(kwargs["Data"])
    assert kinesis_data["type"] == "event"
    assert kinesis_data["data"]["user_id"] == sample_event["user_id"]


def test_identify_event_success(lambda_event_factory, sample_event, mock_kinesis):
    sample_event["prev_user_id"] = "prev_user_id"

    event = lambda_event_factory(path="/identify", body=sample_event)
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    assert json.loads(response["body"])["message"] == "Ok"

    mock_kinesis.put_record.assert_called_once()
    call_args = mock_kinesis.put_record.call_args[1]
    assert call_args["StreamName"] == "test-stream"

    kinesis_data = json.loads(call_args["Data"])
    assert kinesis_data["type"] == "identify"
    assert kinesis_data["data"]["user_id"] == sample_event["user_id"]
    assert kinesis_data["data"]["prev_user_id"] == sample_event["prev_user_id"]


def test_invalid_json_body(lambda_event_factory):
    event = lambda_event_factory(path="/track", body="invalid json")
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    assert "Bad Request" in json.loads(response["body"])["message"]


def test_kinesis_error(lambda_event_factory, sample_event, mock_kinesis):
    mock_kinesis.put_record.side_effect = Exception("Kinesis error")

    event = lambda_event_factory(path="/track", body=sample_event)
    response = lambda_handler(event, {})

    assert response["statusCode"] == 500
    assert json.loads(response["body"])["message"] == "Kinesis error"


def test_response_class():
    response = Response(
        statusCode=200,
        headers={"Content-Type": "application/json"},
        body={"message": "test"},
    )

    lambda_response = response.to_lambda_response()
    assert lambda_response["statusCode"] == 200
    assert lambda_response["headers"] == {"Content-Type": "application/json"}
    assert json.loads(lambda_response["body"]) == {"message": "test"}
