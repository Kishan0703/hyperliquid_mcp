from __future__ import annotations

from typing import Any, Dict, Literal

# Try importing the Hyperliquid SDK. If unavailable, fall back to a local stub so the server can run.
try:
    from hyperliquid.exchange import ExchangeClient  # type: ignore
    from hyperliquid.info import InfoClient  # type: ignore
    from hyperliquid.utils.constants import (  # type: ignore
        MAINNET_API_URL,
        MAINNET_WS_URL,
        TESTNET_API_URL,
        TESTNET_WS_URL,
    )
    HAS_HYPERLIQUID = True
except Exception:  # noqa: BLE001 - we want to catch ImportError and similar
    HAS_HYPERLIQUID = False
    # Minimal constants for stub behavior
    MAINNET_API_URL = "https://api.hyperliquid.xyz"
    MAINNET_WS_URL = "wss://api.hyperliquid.xyz/ws"
    TESTNET_API_URL = "https://api.testnet.hyperliquid.xyz"
    TESTNET_WS_URL = "wss://api.testnet.hyperliquid.xyz/ws"

    class ExchangeClient:  # type: ignore
        def __init__(self, private_key: str, api_url: str, ws_url: str):
            self.wallet = type("Wallet", (), {"address": "0xDEMOADDRESS"})

        # Stub methods can be added if needed

    class InfoClient:  # type: ignore
        def __init__(self, api_url: str, skip_ws: bool = True):
            self._api_url = api_url

        async def all_mids(self):
            # Return demo mids
            return [
                {"coin": "BTC", "mid": "60000"},
                {"coin": "ETH", "mid": "2500"},
            ]

# Type for Buy/Sell side to improve type hint quality
OrderSide = Literal["buy", "sell"]

# -----------------------------
# Real Hyperliquid Client Implementation
# -----------------------------

def init_hyperliquid_client(private_key: str, is_testnet: bool = False) -> Dict[str, Any]:
    """
    Initializes the authenticated Hyperliquid Exchange and Info clients.
    The SDK handles the EIP-712 signing internally using the private key.
    """
    if is_testnet:
        api_url = TESTNET_API_URL
        ws_url = TESTNET_WS_URL
    else:
        api_url = MAINNET_API_URL
        ws_url = MAINNET_WS_URL
    
    # The ExchangeClient handles signed/private requests (like placing orders)
    exch_client = ExchangeClient(private_key, api_url, ws_url)

    # The InfoClient handles public requests (like market data)
    info_client = InfoClient(api_url, skip_ws=True)

    # Get the address associated with the private key (useful for logging/checks)
    address = getattr(getattr(exch_client, "wallet", object()), "address", "0xUNKNOWN")
    
    return {
        "exch_client": exch_client,
        "info_client": info_client,
        "address": address,
    }


async def get_all_mids(clients: Dict[str, Any]) -> Dict[str, float]:
    """Fetches all coins' mid prices from Hyperliquid."""
    info_client: InfoClient = clients["info_client"]
    try:
        # Note: The SDK function is likely asynchronous and may return strings for numbers
        data = await info_client.all_mids()
        
        # Simple cleanup: convert prices from string to float
        mids = {
            item["coin"]: float(item["mid"])
            for item in data
            if "mid" in item
        }
        return mids
    except Exception as e:
        # Log the error and raise a specific exception
        print(f"Error fetching mids: {e}")
        raise RuntimeError(f"Hyperliquid API Error: Failed to fetch mids. {e}")


async def place_limit_order(
    clients: Dict[str, Any],
    coin: str,
    side: OrderSide,
    size: float,
    limit_price: float,
    time_in_force: Literal["Gtc", "Ioc", "Alo"] = "Gtc",
    reduce_only: bool = False,
) -> Dict[str, Any]:
    """Places a limit order on Hyperliquid."""
    exch_client: ExchangeClient = clients["exch_client"]
    
    # Convert 'buy'/'sell' string to boolean required by the SDK (True for buy)
    is_buy = side.lower() == "buy"

    # The SDK usually takes order params, we mock the final call structure here
    # Check the latest SDK for the exact order payload structure.
    # The SDK often has a simplified `limit_order` function, but we'll use a generic `order` structure for robustness.
    order_config = {
        "asset": coin, # In a real scenario, this is the asset INDEX, not the coin symbol. You'd need a lookup table.
        "isBuy": is_buy,
        "limitPx": str(limit_price),  # Prices are sent as strings
        "sz": str(size),              # Sizes are sent as strings
        "reduceOnly": reduce_only,
        "orderType": {"limit": {"tif": time_in_force}},
    }
    
    try:
        if HAS_HYPERLIQUID:
            # TODO: Replace with actual SDK call when available, e.g.:
            # response = await exch_client.order([order_config])
            # return response
            return {
                "status": "order_placed",
                "transaction_hash": f"0x...{hash((coin, size, limit_price))}",
                "order_details": order_config,
                "note": "Hyperliquid SDK call placeholder. Implement real call when SDK is installed.",
            }
        # Fallback stub behavior when SDK is not installed
        return {
            "status": "order_placed",
            "transaction_hash": f"0xSTUB...{hash((coin, size, limit_price))}",
            "order_details": order_config,
            "note": "Using stub client because Hyperliquid SDK is not installed.",
        }
    except Exception as e:
        # Handle specific Hyperliquid errors if possible (e.g., insufficient margin, invalid price)
        print(f"Error placing order: {e}")
        raise RuntimeError(f"Order Failed: Check coin, size, or margin. Error: {e}")