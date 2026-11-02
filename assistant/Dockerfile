# Command Assistant API for docs.simplyblock.io. See README.md.
FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN useradd --system --uid 10001 assistant
# Answer cache across restarts (mount /data), and versions to pre-answer.
ENV ASSISTANT_CACHE_FILE=/data/answer-cache.json     ASSISTANT_PREWARM_VERSIONS=latest,dev
USER assistant
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
