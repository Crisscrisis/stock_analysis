# Stock Analysis Dashboard — 项目说明

## 项目概述

可视化股票分析仪表盘，支持多市场股票数据展示与技术/基本面分析。

## 技术栈

### 前端
- **框架**: React + Vite
- **图表库**: TradingView Lightweight Charts（K线/技术指标）
- **UI 组件**: 待定（优先考虑 shadcn/ui 或 Ant Design）
- **状态管理**: Zustand 或 React Context
- **请求库**: Axios 或 fetch

### 后端
- **框架**: Python + FastAPI
- **数据源**:
  - A股/港股: `akshare`（免费，数据全面）
  - 美股: `yfinance`
  - 备用: `tushare`（需 token）
- **任务调度**: APScheduler（定时刷新数据）
- **缓存**: 内存缓存 or Redis（可选）

## 目录结构

```
stock_analysis/
├── CLAUDE.md
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── routers/
│   │   ├── stocks.py        # 股票数据接口
│   │   ├── indicators.py    # 技术指标接口
│   │   └── fundamentals.py  # 基本面数据接口
│   ├── services/
│   │   ├── data_fetcher.py  # 数据抓取（akshare/yfinance）
│   │   └── calculator.py    # 指标计算（MA/MACD/RSI）
│   ├── models/              # 数据模型
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── StockChart/  # TradingView 图表组件
    │   │   ├── Indicators/  # 技术指标面板
    │   │   ├── Fundamentals/ # 基本面数据面板
    │   │   └── Watchlist/   # 自选股列表
    │   ├── pages/
    │   │   └── Dashboard.jsx
    │   ├── hooks/           # 自定义 hooks
    │   └── api/             # API 调用封装
    ├── package.json
    └── vite.config.js
```

## 关注市场

- **A股**: 沪深两市（akshare 数据源）
- **美股**: NYSE / NASDAQ（yfinance 数据源）
- **港股**: 香港联交所（akshare 数据源）
- **ETF/基金**: 国内外主要 ETF

## 核心功能模块

### 1. 价格走势图
- K线图（OHLCV）和折线图切换
- 支持 1D / 1W / 1M / 3M / 1Y / 全时段
- 成交量柱状图

### 2. 技术指标
- 均线：MA5 / MA10 / MA20 / MA60
- MACD（参数可配置）
- RSI（14日默认）
- 布林带（Bollinger Bands）

### 3. 基本面数据
- 市盈率 PE / 市净率 PB
- 营收 / 净利润（同比增速）
- 股息率
- 总市值 / 流通市值

### 4. 资金流向 / 持仓
- 北向资金（A股）
- 主力资金净流入
- 龙虎榜数据（A股）

## API 设计约定

- Base URL: `http://localhost:8000/api`
- 返回格式统一为 `{ "data": ..., "code": 200, "message": "ok" }`
- 股票代码格式：
  - A股：`600519.SH` / `000001.SZ`
  - 美股：`AAPL`
  - 港股：`00700.HK`

## 开发规范

- 前端组件使用函数式组件 + Hooks
- 后端路由按功能模块拆分，不写在 main.py
- 数据抓取失败要返回明确错误信息，前端要处理加载态和错误态
- 敏感配置（API token 等）放 `.env` 文件，不提交到版本控制

## 启动方式

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```
