FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv==0.11.24

COPY pyproject.toml docker-constraints.txt ./
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "amd64" ]; then \
        uv pip install --system --index-url https://download.pytorch.org/whl/cpu "torch==2.6.0+cpu"; \
    else \
        uv pip install --system "torch==2.6.0"; \
    fi \
    && uv pip install --system --constraint docker-constraints.txt -r pyproject.toml

COPY . .

EXPOSE 8080

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
