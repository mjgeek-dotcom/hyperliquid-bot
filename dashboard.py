
from flask import Flask, jsonify, send_file
import threading
from pymongo import MongoClient
from datetime import datetime, timedelta
import os

app = Flask(__name__)

bot_state = {
    "pnl_state": {},
    "active_orders": {},
    "rsi_values": {},
    "rsi_state": {}
}

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["rsi_bot"]
rsi_collection = db["rsi"]

@app.route("/")
def dashboard_ui():
    return send_file("dashboard.html")

@app.route("/status")
def status():
    filtered = {
        t: {
            "rsi": bot_state["rsi_values"][t],
            "state": bot_state["rsi_state"][t],
            "orders": bot_state["active_orders"].get(t, [])
        }
        for t in bot_state["rsi_state"]
        if bot_state["rsi_state"][t] in ["oversold", "overbought"]
    }
    return jsonify(filtered)

@app.route("/rsi_data")
def rsi_data():
    timestamps = []
    series = {}
    result = rsi_collection.find().sort("timestamp", -1).limit(200)
    for entry in result:
        ts = entry["timestamp"].strftime("%H:%M")
        if ts not in timestamps:
            timestamps.append(ts)
        ticker = entry["ticker"]
        if ticker not in series:
            series[ticker] = []
        series[ticker].append(entry["rsi"])
    timestamps.reverse()
    for ticker in series:
        series[ticker].reverse()
    return jsonify({"timestamps": timestamps, "series": series})

def start_dashboard():
    app.run(host="0.0.0.0", port=8000)



@app.route("/trend_data")
def trend_data():
    rsi_entries = list(rsi_collection.find().sort("timestamp", -1).limit(200))
    timestamps = []
    rsi_series = {}
    price_series = {}

    for entry in reversed(rsi_entries):
        ts = entry["timestamp"].strftime("%H:%M")
        if ts not in timestamps:
            timestamps.append(ts)
        ticker = entry["ticker"]
        rsi = entry["rsi"]
        price = entry.get("price", None)
        if ticker not in rsi_series:
            rsi_series[ticker] = []
            price_series[ticker] = []
        rsi_series[ticker].append(rsi)
        price_series[ticker].append(price if price else 0)

    return jsonify({
        "timestamps": timestamps,
        "rsi_series": rsi_series,
        "price_series": price_series
    })



@app.route("/pnl")
def pnl():
    return jsonify(pnl_state)
