# Stock Analysis Dashboard

可视化股票分析仪表盘，支持多市场数据展示与技术/基本面分析。

## 功能特性

- **价格走势图** — K线图（OHLCV）与折线图切换，支持 1D / 1W / 1M / 3M / 1Y 时间范围，含成交量柱状图
- **技术指标** — MA5/10/20/60、MACD、RSI（14日）、布林带，参数可配置
- **基本面数据** — PE、PB、营收/净利润（同比增速）、股息率、总市值/流通市值
- **资金流向** — 北向资金（A股）、主力净流入、龙虎榜

## 支持市场

| 市场 | 数据源 |
|------|--------|
| A股（沪深） | akshare |
| 港股 | akshare |
| 美股（NYSE/NASDAQ） | yfinance |
| ETF / 基金 | akshare / yfinance |

## Tech Stack

- **Frontend**: React + Vite + TradingView Lightweight Charts
- **Backend**: Python + FastAPI
- **Data**: akshare, yfinance

## 项目结构

```
stock_analysis/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── routers/
│   │   ├── stocks.py        # 股票行情接口
│   │   ├── indicators.py    # 技术指标接口
│   │   └── fundamentals.py  # 基本面数据接口
│   ├── services/
│   │   ├── data_fetcher.py  # 数据抓取（akshare/yfinance）
│   │   └── calculator.py    # 指标计算
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/      # StockChart / Indicators / Fundamentals / Watchlist
    │   ├── pages/
    │   │   └── Dashboard.jsx
    │   ├── hooks/
    │   └── api/
    └── package.json
```

## 快速开始

**后端**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**前端**

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`，后端 API 在 `http://localhost:8000`。

## 环境变量

在 `backend/` 目录下创建 `.env`：

```env
TUSHARE_TOKEN=   # 可选，用于获取更丰富的 A 股数据
```
