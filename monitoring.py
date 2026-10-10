"""Health and Prometheus metrics for Stock Trend Lab."""

import time

from flask import Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS = Counter(
    "sit753_http_requests_total", "Requests served", ["endpoint", "method", "status"]
)
HTTP_ERRORS = Counter(
    "sit753_http_server_errors_total", "HTTP 5xx responses", ["endpoint"]
)
HTTP_LATENCY = Histogram(
    "sit753_http_request_duration_seconds", "Request duration", ["endpoint"]
)


def register_monitoring(app):
    """Attach request metrics and health check routes to a Flask app."""

    @app.before_request
    def begin_request():
        g.request_start = time.perf_counter()

    @app.after_request
    def record_response(response):
        if request.path != "/metrics":
            endpoint = request.url_rule.rule if request.url_rule else "unmatched"
            HTTP_REQUESTS.labels(endpoint, request.method, str(response.status_code)).inc()
            HTTP_LATENCY.labels(endpoint).observe(
                time.perf_counter() - g.get("request_start", time.perf_counter())
            )
            if response.status_code >= 500:
                HTTP_ERRORS.labels(endpoint).inc()
        return response

    @app.get("/health")
    def health():
        return jsonify(service="stock-trend-lab", status="ok")

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)
