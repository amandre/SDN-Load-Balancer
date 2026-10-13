FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create an unprivileged user
RUN groupadd --system app && \
    useradd --system --gid app \
    --home-dir /app \
    --no-create-home \
    --shell /usr/sbin/nologin \
    app

COPY --chown=app:app src/ ./src/
USER app

CMD ["python", "src/lb-topology.py"]
