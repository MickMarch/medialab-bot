FROM python:3.12-slim

ARG APP_VERSION=0.0.0

WORKDIR /app

# git is required at build time: medialab-contracts is a git-ref uv dependency,
# so uv sync must clone it. Kept in the image build only, not a runtime need.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv --no-cache-dir

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-dev --frozen --no-cache --no-install-project

COPY src/ ./src/
RUN SETUPTOOLS_SCM_PRETEND_VERSION=${APP_VERSION} uv sync --no-dev --frozen --no-cache

RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

# No EXPOSE: the bot is an outbound Discord gateway client and an HTTP client of
# the orchestrator; it listens on no port.
CMD ["/app/.venv/bin/medialab-bot"]
