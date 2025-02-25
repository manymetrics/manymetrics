FROM public.ecr.aws/lambda/python:3.12

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml .
COPY uv.lock .

RUN uv pip install --system -r <(uv export --format requirements-txt)

COPY lambda_handler.py .

CMD [ "lambda_handler.lambda_handler" ]
