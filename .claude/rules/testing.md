# Testing

## Backend (pytest)
```bash
cd backend && pytest                  # all tests
cd backend && pytest tests/test_stocks.py  # single file
cd backend && pytest -k "test_name"   # single test
```
- Test files live in `backend/tests/`, mirroring the source structure
- Use `pytest-asyncio` for async route tests
- Mock external data sources (akshare/yfinance) in unit tests; use real calls only in integration tests
- Always run tests after modifying `services/` or `routers/`

## Frontend (Vitest)
```bash
cd frontend && npm run test           # watch mode
cd frontend && npm run test:run       # CI / one-shot
```
- Test files: `*.test.tsx` next to the component
- Test pure logic (hooks, api utils) first; avoid testing TradingView chart rendering
- After every new component, verify with `npm run typecheck`
