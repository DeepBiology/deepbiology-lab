# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY pyproject.toml setup.py README.md LICENSE ./
COPY deepbiology ./deepbiology
COPY deepbiology_lab ./deepbiology_lab

RUN python -m pip wheel --wheel-dir /wheels .


FROM python:3.11-slim-bookworm AS runtime

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    PORT=8000

RUN groupadd --gid 10001 deepbiology \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin deepbiology

COPY --from=builder /wheels /wheels
RUN python -m pip install /wheels/*.whl \
    && rm -rf /wheels

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; response = urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2); assert response.status == 200; response.close()"]

CMD ["deepbiology-lab-mcp"]
