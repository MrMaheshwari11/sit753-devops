"""Stock Trend Lab: a demonstrable Flask API and dashboard for SIT753.

This is a learning example, not a real-time market price or trading service.
"""

import math
import os
import re
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from monitoring import register_monitoring

app = Flask(__name__, static_folder="static")
register_monitoring(app)


def connect_database():
    """Create a SQLite connection and make sure the table exists."""
    filename = Path(os.getenv("DATABASE_PATH", "/tmp/sit753-watchlist.sqlite"))
    filename.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(filename)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS watchlist ("
        "symbol TEXT PRIMARY KEY, added_at TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    connection.commit()
    return connection


@app.get("/")
def index():
    """Dashboard, served with a small browser-based API client."""
    return send_from_directory(app.static_folder, "index.html")


@app.post("/api/predict")
def predict():
    """Moving-average forecast using user-supplied historical observations."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="A JSON object is required."), 400
    prices = payload.get("prices")
    window = payload.get("window", 3)
    if (
        not isinstance(prices, list)
        or len(prices) < 3
        or len(prices) > 365
        or not isinstance(window, int)
        or isinstance(window, bool)
        or not 2 <= window <= len(prices)
        or any(
            not isinstance(value, (float, int))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value <= 0
            for value in prices
        )
    ):
        return jsonify(error="Use 3–365 positive prices and a valid window."), 400
    estimate = sum(prices[-window:]) / window
    latest = prices[-1]
    change_pct = ((estimate - latest) / latest) * 100
    return jsonify(
        forecast=round(estimate, 3),
        latest=latest,
        difference_percent=round(change_pct, 3),
        trend="up" if estimate > latest else "down" if estimate < latest else "flat",
        method=f"{window}-point simple moving average",
    )


@app.get("/api/watchlist")
def read_watchlist():
    """List watchlist symbols stored in SQLite."""
    connection = connect_database()
    try:
        symbols = [row[0] for row in connection.execute(
            "SELECT symbol FROM watchlist ORDER BY symbol"
        )]
    finally:
        connection.close()
    return jsonify(symbols=symbols)


@app.post("/api/watchlist")
def add_to_watchlist():
    """Add a validated symbol without duplicating existing entries."""
    payload = request.get_json(silent=True)
    value = payload.get("symbol") if isinstance(payload, dict) else None
    if not isinstance(value, str):
        return jsonify(error="symbol must be a string"), 400
    symbol = value.strip().upper()
    if not re.fullmatch(r"[A-Z0-9.\-]{1,10}", symbol):
        return jsonify(error="Invalid symbol"), 400
    connection = connect_database()
    try:
        result = connection.execute(
            "INSERT OR IGNORE INTO watchlist(symbol) VALUES (?)", (symbol,)
        )
        connection.commit()
        created = result.rowcount == 1
    finally:
        connection.close()
    return jsonify(symbol=symbol, created=created), 201 if created else 200


@app.delete("/api/watchlist/<symbol>")
def remove_from_watchlist(symbol):
    """Remove a watchlist symbol."""
    normalized = symbol.upper()
    connection = connect_database()
    try:
        result = connection.execute(
            "DELETE FROM watchlist WHERE symbol = ?", (normalized,)
        )
        connection.commit()
        deleted = result.rowcount == 1
    finally:
        connection.close()
    if not deleted:
        return jsonify(error="Symbol not found"), 404
    return jsonify(symbol=normalized, deleted=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
