FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# RUN pip install --no-cache-dir "setuptools==68.2.2" wheel

# Install application dependencies
#COPY requirements.txt .

#RUN apt-get update && \
#    apt-get install -y --no-install-recommends git && \
#    pip install --no-cache-dir -r requirements.txt && \
#    apt-get purge -y --auto-remove git && \
#    rm -rf /var/lib/apt/lists/*

# Create an unprivileged user
RUN groupadd --system app && \
    useradd --system --gid app \
    --home-dir /app \
    --no-create-home \
    --shell /usr/sbin/nologin \
    app

#COPY --chown=app:app src/ ./src/
USER app

CMD ["python", "-c", "print('Hello, World!')"]
#CMD ["python", "src/lb-topology.py"]
