# Hyperliquid MCP Server (FastAPI)

### What this is
- **An MCP server** exposing tools to interact with Hyperliquid via HTTP.
- Built with **FastAPI**; reads your **MetaMask private key** from `.env`.
- Ships with a **stub client** so you can run it without the Hyperliquid SDK. Swap to the real SDK when ready.

### What it does
- `/health`: Health check.
- `/mcp/tools` (POST): Advertises available tools (schemas included).
- `/mcp/call` (POST): Executes tools (`get_all_mids`, `place_limit_order`).

---

## Quick start

1) Create `.env` at repo root:
```
PRIVATE_KEY=replace_with_your_metamask_private_key
```
- Keep `.env` out of version control.
- Use the raw private key (hex), not the seed phrase.

2) Install deps:
```
pip install -r requirements.txt
```

3) Run the server:
```
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

4) Try it:
```
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/mcp/tools -H 'Content-Type: application/json' -d '{}'
curl -s -X POST http://127.0.0.1:8000/mcp/call -H 'Content-Type: application/json' -d '{"toolName":"get_all_mids","arguments":{}}'
```

---

## Tools and schemas

- `get_all_mids`
  - Params: none
  - Returns: `{ [coin: string]: number }`

- `place_limit_order`
  - Params:
    - `coin`: string (e.g. "BTC")
    - `side`: string ("buy" | "sell")
    - `size`: number
    - `limit_price`: number
    - `time_in_force` (optional): "Gtc" | "Ioc" | "Alo" (default "Gtc")
    - `reduce_only` (optional): boolean (default false)

Example call:
```
curl -s -X POST http://127.0.0.1:8000/mcp/call \
  -H 'Content-Type: application/json' \
  -d '{
    "toolName":"place_limit_order",
    "arguments": {"coin":"BTC","side":"buy","size":0.1,"limit_price":60000}
  }'
```

---

## Stub vs real SDK

- By default, `mcp_tools.py` tries to import the Hyperliquid SDK.
  - If present: it will initialize real `ExchangeClient`/`InfoClient` and you can trade on testnet/mainnet.
  - If missing: it falls back to a stub (returns demo mids and mock order responses). No funds, no fees.

Switch networks in `server.py` by passing `is_testnet=True` to `init_hyperliquid_client`.

---

## Security

- Never commit your real private key. `.env` is ignored.
- Prefer running on testnet until you validate end-to-end behavior.

---

## Troubleshooting

- Import warnings (fastapi, pydantic, dotenv):
  - Run `pip install -r requirements.txt`.

- Hyperliquid SDK not found:
  - Server still runs using the stub. To use the real SDK, install the official package and replace stubbed calls as needed.

- 404 Unknown tool:
  - Ensure `toolName` matches exactly: `get_all_mids` or `place_limit_order`.