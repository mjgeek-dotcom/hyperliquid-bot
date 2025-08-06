
async def safe_run():
    while True:
        try:
            await listen_to_candles()
        except Exception as e:
            print("WebSocket error:", e)
            await asyncio.sleep(5)


import os
import asyncio
import websockets
import json
import pandas as pd
import numpy as np
import requests
from dotenv import load_dotenv

from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["rsi_bot"]
orders_collection = db["orders"]
rsi_collection = db["rsi"]

from datetime import datetime, timedelta

# Track filled orders and PnL per ticker
pnl_state = {ticker: {"realized": 0.0, "unrealized": 0.0, "trades": []} for ticker in TICKERS}


def calculate_unrealized_pnl(ticker, current_price):
    unrealized = 0
    for order in order_levels[ticker]:
        entry = order["entry"]
        side = order["side"]
        size = 1
        if side == "buy":
            unrealized += (current_price - entry) * size
        elif side == "sell":
            unrealized += (entry - current_price) * size
    pnl_state[ticker]["unrealized"] = unrealized
    return unrealized

def update_pnl(ticker, fill_price, side, entry_price):
    size = 1  # placeholder per order
    pnl = 0
    if side == "buy":
        pnl = (fill_price - entry_price) * size
    else:
        pnl = (entry_price - fill_price) * size
    pnl_state[ticker]["realized"] += pnl
    pnl_state[ticker]["trades"].append({
        "entry": entry_price,
        "exit": fill_price,
        "side": side,
        "pnl": pnl,
        "timestamp": datetime.utcnow()
    })
    print(f"[PnL] {ticker}: {side.upper()} | Entry {entry_price} → Exit {fill_price} | Δ {pnl:.4f}")


# Parameters
SL_PERCENT = 0.03  # 3% stop-loss
TP_PERCENT = 0.05
TRAILING_TP_PERCENT = 0.02  # 2% trailing take profit
trailing_state = {ticker: {"active": False, "peak": None} for ticker in TICKERS}
  # 5% take-profit

# Track SL/TP for each order
order_levels = {ticker: [] for ticker in TICKERS}

def submit_tracked_orders(ticker, side, price, orders):
    now = datetime.utcnow()
    tracked = []
    for order in orders:
        oid = order.get("oid")
        if oid:
            sl = price * (1 - SL_PERCENT) if side == "buy" else price * (1 + SL_PERCENT)
            tp = price * (1 + TP_PERCENT) if side == "buy" else price * (1 - TP_PERCENT)
            tracked.append({
                "oid": oid,
                "timestamp": now,
                "side": side,
                "entry": price,
                "sl": sl,
                "tp": tp
            })
    order_levels[ticker].extend(tracked)
    return tracked

def 
        if rsi > OVERBOUGHT_THRESHOLD:
            print(f"[RSI] {ticker} is OVERBOUGHT (RSI={rsi:.2f})")
            if not alert_state[ticker]["overbought"]:
                alert_state[ticker]["overbought"] = True
                message = f":warning: {ticker} is *OVERBOUGHT* (RSI={rsi:.2f}) - Trailing TP active"
                send_discord_alert(message)
                trailing_state[ticker]["active"] = True
                trailing_state[ticker]["peak"] = close_price
            else:
                print(f"[RSI] {ticker} overbought alert already active")

            # Update trailing peak
            if trailing_state[ticker]["active"]:
                if close_price > trailing_state[ticker]["peak"]:
                    trailing_state[ticker]["peak"] = close_price

                # Check for drop from peak
                drop = (trailing_state[ticker]["peak"] - close_price) / trailing_state[ticker]["peak"]
                if drop >= TRAILING_TP_PERCENT:
                    print(f"[TP] Trailing TP hit for {ticker}, closing orders")
                    for order in list(order_levels[ticker]):
                        exchange.cancel(order["oid"])
                        update_pnl(ticker, close_price, order["side"], order["entry"])
                        order_levels[ticker].remove(order)
                    trailing_state[ticker]["active"] = False
                    send_discord_alert(f":money_with_wings: {ticker} Trailing TP executed!")
            continue
    check_sl_tp(ticker, current_price):
    updated = []
    for order in order_levels[ticker]:
        if order["side"] == "buy":
            if current_price <= order["sl"] or current_price >= order["tp"]:
                print(f"SL/TP hit for BUY order {order['oid']} on {ticker}")
                try:
                    exchange.cancel(order["oid"])
                except:
                    pass
            else:
                updated.append(order)
        elif order["side"] == "sell":
            if current_price >= order["sl"] or current_price <= order["tp"]:
                print(f"SL/TP hit for SELL order {order['oid']} on {ticker}")
                try:
                    exchange.cancel(order["oid"])
                except:
                    pass
            else:
                updated.append(order)
    order_levels[ticker] = updated


volume_history = {ticker: [] for ticker in TICKERS}
price_history = {ticker: [] for ticker in TICKERS}
VOLUME_WINDOW = 5

def detect_trend(ticker, volume, close_price):
    volume_history[ticker].append(volume)
    price_history[ticker].append(close_price)

    if len(volume_history[ticker]) > VOLUME_WINDOW:
        volume_history[ticker].pop(0)
        price_history[ticker].pop(0)

    avg_volume = sum(volume_history[ticker]) / len(volume_history[ticker])
    if volume > 1.5 * avg_volume:
        print(f"Volume spike detected for {ticker}: {volume:.2f} > avg {avg_volume:.2f}")
        send_discord_alert(f"📊 **Volume spike** for {ticker}: {volume:.2f} > avg {avg_volume:.2f}")

    if len(price_history[ticker]) >= 2:
        delta = price_history[ticker][-1] - price_history[ticker][0]
        if abs(delta / price_history[ticker][0]) > 0.02:
            direction = "up" if delta > 0 else "down"
            send_discord_alert(f"📈 **Price trend** for {ticker}: {direction} {delta:.2f}")


ORDER_TIMEOUTS.get(ticker, timedelta(minutes=30))S = {
    "BTC": timedelta(minutes=15),
    "ETH": timedelta(minutes=20),
    "ENA": timedelta(minutes=25),
    "AAVE": timedelta(minutes=30),
    "HYPE": timedelta(minutes=30),
}

from hyperliquid.exchange import Exchange

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
INTERVAL = "1h"
TICKERS = ["BTC", "ETH", "ENA", "AAVE", "HYPE"]

# Hyperliquid credentials

def submit_skewed_limit_sell_orders(ticker, mark_price):
    try:
        base_size = 1.0
        price_step = 0.002  # 0.2% steps above current price
        orders = []
        for i in range(50):
            price = round(mark_price * (1 + price_step * i), 2)
            size = round(base_size * (1 + i * 0.05), 4)  # Increase size with depth
            order = {
                "coin": ticker,
                "isBuy": False,
                "sz": str(size),
                "limitPx": str(price),
                "orderType": "limit"
            }
            orders.append(order)
        response = exchange.bulk_orders(orders)
        print(f"Submitted {len(orders)} sell orders for {ticker}")
        return response
    except Exception as e:
        print(f"Sell order submission failed for {ticker}:", e)

ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")
SECRET_KEY = os.getenv("SECRET_KEY")

exchange = Exchange(account_address=ACCOUNT_ADDRESS, priv_key=SECRET_KEY)

candles_dict = {ticker: [] for ticker in TICKERS}
last_alert_state = {ticker: None for ticker in TICKERS}

def calculate_rsi(prices, period=14):
    delta = np.diff(prices)
    gain = np.maximum(delta, 0)
    loss = np.maximum(-delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.isna().all() else None

def send_discord_alert(ticker, rsi_value, condition):
    msg = f"⚠️ RSI Alert for {ticker}: RSI = {rsi_value:.2f} ({condition.upper()}, {INTERVAL})"
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})
    except Exception as e:
        print("Failed to send Discord webhook:", e)

def submit_skewed_limit_orders(ticker, mark_price):
    try:
        base_size = 1.0
        price_step = 0.002  # 0.2% steps below current price
        orders = []
        for i in range(50):
            price = round(mark_price * (1 - price_step * i), 2)
            size = round(base_size * (1 + i * 0.05), 4)  # Increase size with depth
            order = {
                "coin": ticker,
                "isBuy": True,
                "sz": str(size),
                "limitPx": str(price),
                "orderType": "limit"
            }
            orders.append(order)
        response = exchange.bulk_orders(orders)
        print(f"Submitted {len(orders)} orders for {ticker}")
        return response
    except Exception as e:
        print(f"Order submission failed for {ticker}:", e)


placed_orders = {ticker: [] for ticker in TICKERS}
bot_state["active_orders"] = placed_orders
bot_state["rsi_values"] = {ticker: None for ticker in TICKERS}
bot_state["rsi_state"] = {ticker: None for ticker in TICKERS}


def cancel_expired_orders(ticker):
    now = datetime.utcnow()
    active = []
    for oid, ts in placed_orders[ticker]:
        if now - ts > ORDER_TIMEOUTS.get(ticker, timedelta(minutes=30)):
            try:
                exchange.cancel(oid)
                print(f"Cancelled expired order {oid} for {ticker}")
            except Exception as e:
                print(f"Error canceling order {oid}:", e)
        else:
            active.append((oid, ts))
    placed_orders[ticker] = active

def track_orders(response, ticker):
    now = datetime.utcnow()
    try:
        if isinstance(response, list):
            for order in response:
                if "oid" in order:
                    placed_orders[ticker].append((order["oid"], now))
    except Exception as e:
        print(f"Tracking error:", e)


async def listen_to_candles():
    print("WebSocket connection established")
    uri = "wss://api.hyperliquid.xyz/ws"
    async with websockets.connect(uri) as ws:
        for idx, ticker in enumerate(TICKERS):
            subscription_msg = {
                "method": "subscribe",
                "topic": f"candle.{ticker}.{INTERVAL}",
                "id": idx + 1
            }
            await ws.send(json.dumps(subscription_msg))

        while True:
            try:
                message = await ws.recv()
                data = json.loads(message)

                if "topic" in data and "data" in data:
                    topic_parts = data["topic"].split(".")
                    if len(topic_parts) != 3:
                        continue
                    ticker = topic_parts[1]
                    candle = data["data"]
                    close_price = float(candle["close"])
                    timestamp = int(candle["time"])

                    candle_list = candles_dict[ticker]
                    if not candle_list or candle_list[-1][0] != timestamp:
                        candle_list.append((timestamp, close_price))
                        if len(candle_list) > RSI_PERIOD + 1:
                            candle_list.pop(0)

                        if len(candle_list) >= RSI_PERIOD + 1:
                            closes = [c[1] for c in candle_list]
                            rsi = calculate_rsi(closes, RSI_PERIOD)

try:
    rsi_collection.insert_one({
        "ticker": ticker,
        "rsi": rsi,
        "timestamp": datetime.utcnow()
    })
except Exception as e:
    print("Mongo logging error:", e)

                            if rsi is not None:
                                last_state = last_alert_state[ticker]
                                if rsi < RSI_OVERSOLD and last_state != "oversold":
                                    send_discord_alert(ticker, rsi, "oversold")
                                    orders = submit_skewed_limit_orders(ticker, close_price); track_orders(orders, ticker); submit_tracked_orders(ticker, "buy", close_price, orders)
                                    last_alert_state[ticker] = "oversold"
                                    bot_state["rsi_state"][ticker] = "oversold"
                                elif rsi > RSI_OVERBOUGHT and last_state != "overbought":
                                    send_discord_alert(ticker, rsi, "overbought")
                                    orders = submit_skewed_limit_sell_orders(ticker, close_price); track_orders(orders, ticker); submit_tracked_orders(ticker, "sell", close_price, orders)
                                    last_alert_state[ticker] = "overbought"
                                    bot_state["rsi_state"][ticker] = "overbought"
                                elif RSI_OVERSOLD <= rsi <= RSI_OVERBOUGHT:
                                    last_alert_state[ticker] = None
                                    bot_state["rsi_state"][ticker] = "normal"
                                cancel_expired_orders(ticker)

            except Exception as e:
                print("Error:", e)
                await asyncio.sleep(5)


if __name__ == "__main__":
    from dashboard import start_dashboard
    threading.Thread(target=start_dashboard, daemon=True).start()

    asyncio.run(safe_run())
        
        if rsi < OVERSOLD_THRESHOLD:
            print(f"[RSI] {ticker} is OVERSOLD (RSI={{rsi:.2f}})")
            if not alert_state[ticker]["oversold"]:
                alert_state[ticker]["oversold"] = True
                message = f":warning: {{ticker}} is *OVERSOLD* (RSI={{rsi:.2f}})"
                send_discord_alert(message)

                # Place 50 limit BUY orders at $10 each
                base_price = close_price
                for i in range(50):
                    price = round(base_price * (1 - i * 0.001), 4)
                    size = round(10 / price, 6)  # 10 USDC per order
                    side = "buy"
                    oid = exchange.place_order(ticker, side, price, size)
                    order_levels[ticker].append({
                        "oid": oid,
                        "entry": price,
                        "side": side,
                        "placed_at": datetime.utcnow()
                    })
                print(f"[ORDER] Placed 50 BUY orders of $10 each for {{ticker}}")
            else:
                print(f"[RSI] {{ticker}} oversold alert already active")
            continue  # Skip further logic for oversold state

    
