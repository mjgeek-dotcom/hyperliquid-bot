# hyperliquid_api.py
import aiohttp
from config import Config

class HyperliquidAPI:
    def __init__(self):
        self.base_url = "https://api.hyperliquid.xyz"
        self.headers = {"Authorization": f"Bearer {Config.API_KEY}"}

    async def get_balance(self):
        async with aiohttp.ClientSession() as session:
            payload = {
                "type": "clearinghouseState",
                "user": Config.WALLET
            }
            async with session.post(f"{self.base_url}/info", json=payload, headers=self.headers) as resp:
                return await resp.json()

    async def submit_order(self, symbol, side, size):
        order = {
            "symbol": symbol,
            "side": side,
            "size": str(size),
            "type": "market",
            "reduceOnly": False
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/order", json=order, headers=self.headers) as resp:
                return await resp.json()