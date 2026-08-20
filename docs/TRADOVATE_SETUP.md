# Tradovate API Setup

The scanner needs read access to OHLC bar history and live bar updates for
MNQ and MGC. It never places, modifies, or cancels an order — read-only
market data access is all it needs.

## Steps

1. **Apply for API access.** Tradovate's API requires a developer
   application. Go to Tradovate's developer/API portal (linked from your
   Tradovate account settings) and register an application to get a
   `clientId` / `clientSecret`. Note: this is separate from your regular
   Tradovate login.
2. **Confirm market-data entitlement.** Ask Tradovate support (or check
   your account's data subscriptions) whether your plan includes API
   access to live CME futures market data (MNQ/MGC), or whether a separate
   real-time data subscription is required. Do not assume this is free —
   confirm before relying on it.
3. **Confirm demo vs. live.** Determine whether your Apex evaluation/PA
   account trades through Tradovate's **demo** environment or a **live**
   funded environment — this determines the API base URL
   (`demo.tradovateapi.com` vs `live.tradovateapi.com`) and which
   credentials to use. If you run both an eval and a PA account
   simultaneously, you may need two separate connections.
4. **Fill in `.env`:**
   ```
   TRADOVATE_ENV=demo   # or live
   TRADOVATE_CLIENT_ID=...
   TRADOVATE_CLIENT_SECRET=...
   TRADOVATE_USERNAME=...
   TRADOVATE_PASSWORD=...
   ```
5. **Test the connection:**
   ```
   python -m scanner.main --check-connection
   ```
   This authenticates and fetches a small amount of recent MNQ bar history
   without starting the live scan loop.

## Reference

`scanner/data/tradovate_client.py` implements OAuth token acquisition, a
REST call for historical bars, and a WebSocket subscription for live bar
closes. See Tradovate's official API docs for the current endpoint paths
and payload shapes if anything here needs adjusting — API details can
change and should be verified against their live documentation rather than
assumed correct indefinitely.
