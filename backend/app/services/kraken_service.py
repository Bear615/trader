"""
Kraken REST API service — used exclusively when trading_mode == 'live'.

Implements HMAC-SHA512 authenticated requests per the Kraken API docs.
API keys are NEVER written to logs.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
import urllib.parse
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

KRAKEN_BASE = "https://api.kraken.com"
_PUBLIC_PATH = "/0/public"
_PRIVATE_PATH = "/0/private"


# ---------------------------------------------------------------------------
# Signature helpers
# ---------------------------------------------------------------------------

def _nonce() -> str:
    return str(int(time.time() * 1000))


def _sign(urlpath: str, data: dict, secret: str) -> str:
    """
    Generate Kraken HMAC-SHA512 signature.
    signature = HMAC-SHA512(urlpath + SHA-256(nonce + post_data), base64_decode(secret))
    """
    post_data = urllib.parse.urlencode(data)
    encoded = (data["nonce"] + post_data).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()


# ---------------------------------------------------------------------------
# Low-level request helpers
# ---------------------------------------------------------------------------

def _check_errors(data: dict) -> None:
    """Raise if Kraken returned a non-empty error list."""
    errors = data.get("error", [])
    if errors:
        raise RuntimeError(f"Kraken API error: {'; '.join(errors)}")


async def _public_get(endpoint: str, params: Optional[dict] = None) -> dict:
    url = f"{KRAKEN_BASE}{_PUBLIC_PATH}/{endpoint}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
    data = resp.json()
    _check_errors(data)
    return data.get("result", {})


async def _private_post(endpoint: str, payload: dict, api_key: str, api_secret: str) -> dict:
    urlpath = f"{_PRIVATE_PATH}/{endpoint}"
    url = f"{KRAKEN_BASE}{urlpath}"
    payload["nonce"] = _nonce()
    signature = _sign(urlpath, payload, api_secret)
    headers = {
        "API-Key": api_key,
        "API-Sign": signature,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, data=payload, headers=headers)
        resp.raise_for_status()
    data = resp.json()
    _check_errors(data)
    return data.get("result", {})


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

async def get_ticker(pair: str) -> dict:
    """
    Fetch ticker for *pair* (e.g. 'XXRPZUSD').
    Returns {price, bid, ask, volume_24h}.
    """
    result = await _public_get("Ticker", {"pair": pair})
    # Kraken may return the pair under an alias key; grab the first value
    ticker = next(iter(result.values()))
    return {
        "price":      float(ticker["c"][0]),   # last trade price
        "bid":        float(ticker["b"][0]),
        "ask":        float(ticker["a"][0]),
        "volume_24h": float(ticker["v"][1]),    # rolling 24-h volume
    }


# ---------------------------------------------------------------------------
# Private / authenticated helpers
# ---------------------------------------------------------------------------

async def get_balances(api_key: str, api_secret: str, quote_currency: str = "USD") -> dict:
    """
    Fetch account balances.
    Returns {usd: float, quote: float, quote_currency: str, xrp: float}.
    The legacy `usd` key contains the selected quote-currency balance so older
    portfolio fields can keep working without a database migration.
    """
    result = await _private_post("Balance", {}, api_key, api_secret)

    def normalized_asset(asset: str) -> str:
        base = asset.upper().split(".", 1)[0]
        if base.startswith(("X", "Z")) and len(base) > 3:
            return base[1:]
        return base

    def total_for(*aliases: str) -> float:
        wanted = {alias.upper() for alias in aliases}
        total = 0.0
        for asset, raw_amount in result.items():
            if normalized_asset(asset) in wanted:
                try:
                    total += float(raw_amount)
                except (TypeError, ValueError):
                    logger.warning("Ignoring non-numeric Kraken balance for asset %s", asset)
        return total

    quote = quote_currency.upper()

    # Kraken may label assets as ZUSD, USD, XXRP, XRP, ZGBP, GBP, or suffixed forms like ZUSD.F.
    xrp = total_for("XRP")
    quote_balance = total_for(quote)
    return {"usd": quote_balance, "quote": quote_balance, "quote_currency": quote, "xrp": xrp}


async def place_order(
    pair: str,
    side: str,          # "buy" | "sell"
    volume: float,
    order_type: str,    # "market" | "limit"
    api_key: str,
    api_secret: str,
    limit_price: Optional[float] = None,
) -> dict:
    """
    Place a Kraken order. Returns {order_id, status, filled_price}.
    filled_price is the last ticker price at submission for market orders
    (the actual fill price is only known after the order settles).
    """
    payload: dict[str, Any] = {
        "pair":      pair,
        "type":      side.lower(),
        "ordertype": order_type.lower(),
        # Kraken XRP lot size: 2 decimal places maximum
        "volume":    f"{volume:.2f}",
    }
    if order_type.lower() == "limit":
        if limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        payload["price"] = f"{limit_price:.6f}"

    result = await _private_post("AddOrder", payload, api_key, api_secret)
    txids = result.get("txid", [])
    order_id = txids[0] if txids else None

    # For market orders, poll once for the actual fill price (best effort, short wait)
    filled_price: float
    if order_id and order_type.lower() == "market":
        import asyncio
        await asyncio.sleep(1.5)  # brief wait for Kraken to settle the market order
        try:
            status = await get_order_status(order_id, api_key, api_secret)
            filled_price = status["price"] if status["price"] > 0 else (await get_ticker(pair))["price"]
        except Exception:
            filled_price = (await get_ticker(pair))["price"]
    else:
        # Limit order: use the stated limit price as the fill price
        filled_price = limit_price if limit_price else (await get_ticker(pair))["price"]

    logger.info("Kraken order placed: side=%s volume=%s type=%s order_id=%s", side, volume, order_type, order_id)
    return {
        "order_id":     order_id,
        "status":       "open",
        "filled_price": filled_price,
    }


async def get_order_status(order_id: str, api_key: str, api_secret: str) -> dict:
    """Query the status of a specific order by txid."""
    result = await _private_post("QueryOrders", {"txid": order_id, "trades": True}, api_key, api_secret)
    order = result.get(order_id, {})
    return {
        "order_id": order_id,
        "status":   order.get("status", "unknown"),
        "vol_exec": float(order.get("vol_exec", 0)),
        "price":    float(order.get("price", 0)),
    }
