# Stock Analysis Dashboard

# Rules
@.claude/rules/code-style.md
@.claude/rules/testing.md
@.claude/rules/security.md

## Tech Stack
- Frontend: React + Vite + TradingView Lightweight Charts
- Backend: Python + FastAPI
- Data: akshare (A股/港股/ETF), yfinance (美股)

## Dev Commands

```bash
# Backend
cd backend && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Run backend tests
cd backend && pytest

# Run frontend type check
cd frontend && npm run typecheck
```

## Non-obvious Conventions

**Stock symbol format** — be consistent across all layers:
- A股: `600519.SH` / `000001.SZ`
- 港股: `00700.HK`
- 美股: `AAPL`

**API response envelope** — always wrap responses:
```json
{ "data": ..., "code": 200, "message": "ok" }
```
On error: `{ "data": null, "code": 4xx, "message": "<reason>" }`

**Data source routing** — never mix sources for the same market:
- A股 + 港股 + 国内ETF → akshare only
- 美股 + 海外ETF → yfinance only
- Do NOT fall back to the other source on failure; return an error instead

**Technical indicators** — calculate server-side in `backend/services/calculator.py`, never in the frontend.

## Environment Variables

Backend requires a `.env` file in `backend/`:
```
TUSHARE_TOKEN=   # optional, for premium A股 data
```

## Gotchas
- akshare A股 historical data uses `sh600519` format internally; convert to/from `600519.SH` at the service boundary
- TradingView Lightweight Charts requires OHLCV timestamps in **seconds** (Unix), not milliseconds
- `uvicorn` must run from inside `backend/` so relative imports resolve correctly
