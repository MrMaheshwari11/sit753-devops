FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN groupadd -r appuser && useradd -r -m -d /home/appuser -g appuser appuser
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY app.py monitoring.py /app/
COPY static /app/static
RUN mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
ENV DATABASE_PATH=/app/data/watchlist.sqlite
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "app:app"]
