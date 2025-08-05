from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    API_KEY = os.getenv("HYPERLIQUID_API_KEY")
    WALLET = os.getenv("WALLET_ADDRESS")
    DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
    RISK_PCT = float(os.getenv("RISK_PER_TRADE", 0.02))
    TESTNET = True  # Set to False for mainnet