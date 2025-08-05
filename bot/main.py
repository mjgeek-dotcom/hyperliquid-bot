# main.py
import asyncio
from indicators import calculate_rsi, calculate_atr
from risk_engine import DynamicRiskEngine
from hyperliquid_api import HyperliquidAPI

class TradingBot:
    def __init__(self):
        self.api = HyperliquidAPI()
        self.risk_engine = DynamicRiskEngine()
        self.symbol = "HYPE/USDC"

    async def run(self):
        while True:
            # 1. Sync balance
            balance = await self.api.get_balance()
            
            # 2. Get market data
            candles = await self.fetch_candles()
            
            # 3. Calculate indicators
            rsi = calculate_rsi(candles['close'])
            atr = calculate_atr(candles)
            
            # 4. Dynamic risk adjustment
            risk_pct = self.risk_engine.calculate_risk(
                drawdown=self.risk_engine.current_drawdown,
                consecutive_losses=self.risk_engine.consecutive_losses
            )
            
            # 5. Generate signals
            if rsi[-1] < 35:  # Oversold
                size = self.calculate_position_size(atr, risk_pct, balance)
                await self.api.submit_order(self.symbol, "buy", size)


#Discord Alerts

from discord_webhook import DiscordWebhook

async def send_alert(message):
    webhook = DiscordWebhook(url=Config.DISCORD_WEBHOOK, content=message)
    webhook.execute()


#Health Checks
async def health_check():
    while True:
        await asyncio.sleep(3600)
        if not self.api.ping():
            await send_alert("🔴 Bot offline - restart required")


# Emergency stop
MAX_DAILY_LOSS = -0.2  # -20%
if self.risk_engine.current_drawdown > abs(MAX_DAILY_LOSS):
    await self.api.cancel_all_orders()
    await send_alert("🛑 EMERGENCY STOP: Max drawdown exceeded")