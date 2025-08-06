# bot/main.py
import os
import asyncio
import numpy as np
from discord_webhook import DiscordWebhook
import websockets
import aiohttp
from dotenv import load_dotenv
from collections import deque

load_dotenv()

class GridTradingBot:
    def __init__(self):
        # Configuration
        self.symbol = os.getenv("SYMBOL", "HYPE")
        self.quote = os.getenv("QUOTE", "USDC")
        self.pair = f"{self.symbol}/{self.quote}"
        self.ws_url = os.getenv("WS_URL", "wss://api.hyperliquid.xyz/ws")
        self.api_url = os.getenv("API_URL", "https://api.hyperliquid.xyz")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK")
        
        # Trading parameters
        self.rsi_period = int(os.getenv("RSI_PERIOD", 14))
        self.overbought = float(os.getenv("OVERBOUGHT", 65))
        self.oversold = float(os.getenv("OVERSOLD", 35))
        
        # Grid configuration
        self.grid_levels = 100  # Fixed 100 orders
        self.entry_spread = float(os.getenv("ENTRY_SPREAD", 0.02))  # 2% between orders
        self.tp_spread = float(os.getenv("TP_SPREAD", 0.01))  # 1% TP steps
        self.stop_loss = float(os.getenv("STOP_LOSS", 0.95))  # 5% SL
        
        # Risk management
        self.max_drawdown = float(os.getenv("MAX_DRAWDOWN", 0.1))
        self.consecutive_losses = 0
        self.equity_curve = deque(maxlen=1000)
        
        # State tracking
        self.candles = []
        self.active_orders = []
        self.session = aiohttp.ClientSession()
        self.headers = {
            "Authorization": f"Bearer {os.getenv('API_KEY')}",
            "Content-Type": "application/json"
        }

    async def calculate_rsi(self) -> float:
        """Calculate RSI from 5-minute candles"""
        if len(self.candles) < self.rsi_period + 1:
            return 50  # Neutral until we have enough data
            
        closes = [c['close'] for c in self.candles[-self.rsi_period-1:]]
        deltas = np.diff(closes)
        gains = deltas[deltas >= 0]
        losses = -deltas[deltas < 0]
        
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 1e-10  # Avoid division by zero
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    async def generate_grid(self, current_price: float) -> tuple:
        """Create 100 entry levels and corresponding TP levels"""
        entry_prices = np.linspace(
            current_price * (1 - self.entry_spread),
            current_price * (1 - self.entry_spread * self.grid_levels),
            self.grid_levels
        )
        
        tp_levels = []
        for entry in entry_prices:
            num_tps = int((1 - self.stop_loss) / self.tp_spread)
            tp_levels.append([entry * (1 + i*self.tp_spread) for i in range(1, num_tps+1)])
            
        return entry_prices, tp_levels

    async def place_grid_orders(self):
        """Place 100 limit orders with cascading TPs"""
        if len(self.candles) < 2:
            return
            
        current_price = self.candles[-1]['close']
        rsi = await self.calculate_rsi()
        
        # Only place orders when RSI indicates opportunity
        if rsi > self.overbought or rsi < self.oversold:
            await self.cancel_all_orders()
            return
            
        entry_prices, tp_levels = await self.generate_grid(current_price)
        risk_pct = await self.calculate_dynamic_risk()
        total_size = (await self.get_balance() * risk_pct) / current_price
        order_size = total_size / self.grid_levels
        
        for i, (entry_price, tps) in enumerate(zip(entry_prices, tp_levels)):
            # Place entry order
            entry_order = {
                "symbol": self.pair,
                "side": "buy",
                "type": "limit",
                "price": str(entry_price),
                "size": str(order_size),
                "reduceOnly": False,
                "cloid": f"entry_{i}"
            }
            await self.submit_order(entry_order)
            
            # Store TP levels for later
            self.active_orders.append({
                "entry_price": entry_price,
                "size": order_size,
                "tp_levels": tps
            })
            
        await self.send_alert(
            f"📊 100-LAYER GRID DEPLOYED\n"
            f"Current Price: ${current_price:.4f}\n"
            f"RSI: {rsi:.1f}\n"
            f"Risk: {risk_pct*100:.1f}%"
        )

    async def run(self):
        async with websockets.connect(self.ws_url) as ws:
            await ws.send(json.dumps({
                "method": "SUBSCRIBE",
                "params": [f"{self.symbol.lower()}@kline_5m"],
                "id": 1
            }))
            
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                
                if 'kline' in data and data['kline']['interval'] == '5m':
                    candle = {
                        'open': float(data['kline']['open']),
                        'high': float(data['kline']['high']),
                        'low': float(data['kline']['low']),
                        'close': float(data['kline']['close']),
                        'volume': float(data['kline']['volume']),
                        'timestamp': data['kline']['timestamp']
                    }
                    self.candles.append(candle)
                    await self.place_grid_orders()

if __name__ == "__main__":
    bot = GridTradingBot()
    asyncio.run(bot.run())
