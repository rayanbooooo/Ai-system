"""Read-only Tradovate REST + WebSocket client for OHLC bar data.

This client only ever requests market data - it never places, modifies,
or cancels an order. Endpoint paths and payload shapes follow Tradovate's
publicly documented API as of this writing; Tradovate has changed these
before, so if anything here 404s or the response shape doesn't match,
cross-check against their current docs (https://api.tradovate.com) rather
than assuming this file is still accurate. See docs/TRADOVATE_SETUP.md.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import requests
import websockets

from scanner.structure.models import Bar

DEMO_REST = "https://demo.tradovateapi.com/v1"
LIVE_REST = "https://live.tradovateapi.com/v1"
DEMO_MD_WS = "wss://md-demo.tradovateapi.com/v1/websocket"
LIVE_MD_WS = "wss://md.tradovateapi.com/v1/websocket"

_TOKEN_LIFETIME_SECONDS = 55 * 60  # Tradovate tokens are typically ~70min; refresh a bit early


class TradovateAuthError(RuntimeError):
    pass


class TradovateClient:
    def __init__(self, settings) -> None:
        self._settings = settings.tradovate
        self._rest_base = DEMO_REST if self._settings.env == "demo" else LIVE_REST
        self._md_ws_url = DEMO_MD_WS if self._settings.env == "demo" else LIVE_MD_WS
        self._access_token: str | None = None
        self._md_access_token: str | None = None
        self._token_expires_at: float = 0.0

    def authenticate(self) -> None:
        payload = {
            "name": self._settings.username,
            "password": self._settings.password,
            "appId": self._settings.app_id,
            "appVersion": self._settings.app_version,
            "cid": self._settings.client_id,
            "sec": self._settings.client_secret,
            "deviceId": "ai-system-scanner",
        }
        resp = requests.post(f"{self._rest_base}/auth/accesstokenrequest", json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if "accessToken" not in data:
            raise TradovateAuthError(f"Tradovate auth failed: {data}")
        self._access_token = data["accessToken"]
        self._md_access_token = data.get("mdAccessToken", data["accessToken"])
        self._token_expires_at = time.time() + _TOKEN_LIFETIME_SECONDS

    def _ensure_authenticated(self) -> None:
        if self._access_token is None or time.time() >= self._token_expires_at:
            self.authenticate()

    def fetch_history_bars(self, symbol: str, timeframe: str, bars_back: int = 500) -> list[Bar]:
        """Fetch recent historical bars for `symbol` at `timeframe`
        ("1m", "15m", "1h"). Used to seed the swing/structure detection
        pipeline before switching to live streaming.
        """
        self._ensure_authenticated()
        elem_size, elem_unit = _timeframe_to_element(timeframe)
        payload = {
            "symbol": symbol,
            "chartDescription": {
                "underlyingType": "MinuteBar",
                "elementSize": elem_size,
                "elementSizeUnit": elem_unit,
                "withHistogram": False,
            },
            "timeRange": {"asMuchAsElements": bars_back},
        }
        headers = {"Authorization": f"Bearer {self._md_access_token}"}
        resp = requests.post(f"{self._rest_base}/md/getChart", json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        raw_bars = resp.json().get("bars", [])
        return [_bar_from_raw(i, b) for i, b in enumerate(raw_bars)]

    async def stream_live_bars(self, symbol: str, timeframe: str, on_bar) -> None:
        """Long-lived WebSocket subscription. Calls `on_bar(Bar)` for each
        closed bar. Runs until the connection is closed or the task is
        cancelled by the caller.
        """
        self._ensure_authenticated()
        elem_size, elem_unit = _timeframe_to_element(timeframe)
        async with websockets.connect(self._md_ws_url) as ws:
            await ws.send(f"authorize\n0\n\n{self._md_access_token}")
            await ws.recv()  # auth ack

            sub_payload = {
                "symbol": symbol,
                "chartDescription": {
                    "underlyingType": "MinuteBar",
                    "elementSize": elem_size,
                    "elementSizeUnit": elem_unit,
                },
            }
            await ws.send(f"md/subscribeChart\n1\n\n{json.dumps(sub_payload)}")

            index = 0
            async for message in ws:
                bar = _parse_ws_chart_message(message, index)
                if bar is not None:
                    index += 1
                    on_bar(bar)


def _timeframe_to_element(timeframe: str) -> tuple[int, str]:
    mapping = {
        "1m": (1, "Minute"),
        "15m": (15, "Minute"),
        "1h": (60, "Minute"),  # verify: some Tradovate API versions expose an hour unit directly - check current docs
    }
    if timeframe not in mapping:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return mapping[timeframe]


def _bar_from_raw(index: int, raw: dict) -> Bar:
    ts_raw = raw.get("timestamp")
    if isinstance(ts_raw, (int, float)):
        ts = datetime.fromtimestamp(ts_raw / 1000, tz=timezone.utc)
    else:
        ts = datetime.fromisoformat(ts_raw)
    return Bar(index=index, timestamp=ts, open=raw["open"], high=raw["high"], low=raw["low"], close=raw["close"])


def _parse_ws_chart_message(message: str, index: int) -> Bar | None:
    # Tradovate's WebSocket protocol frames messages with a type-character
    # prefix ('a' for arrays of events, 'o'/'c'/'h' for open/close/heartbeat).
    # This parses the 'a' case for a chart data event. Best-effort scaffold
    # from documented behavior - confirm exact framing against a live
    # connection and adjust if event/field names differ.
    if not message or message[0] != "a":
        return None
    try:
        body = json.loads(message[1:])
    except (ValueError, IndexError):
        return None
    if not isinstance(body, list):
        return None
    for event in body:
        if not isinstance(event, dict) or event.get("e") != "chart":
            continue
        charts = event.get("d", {}).get("charts", [])
        if charts and charts[0].get("bars"):
            return _bar_from_raw(index, charts[0]["bars"][-1])
    return None
