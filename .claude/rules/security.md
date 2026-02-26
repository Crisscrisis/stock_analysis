# Security

- NEVER commit `.env` files or any file containing tokens/keys
- API tokens (TUSHARE_TOKEN, etc.) must only be read from environment variables, never hardcoded
- FastAPI CORS: restrict `allow_origins` to `localhost` in dev; set explicitly in production — do NOT use `*`
- Validate all stock symbol inputs server-side before passing to akshare/yfinance (prevent injection via symbol strings)
- Do not expose raw akshare/yfinance error messages to the frontend; log server-side, return generic error to client
