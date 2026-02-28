# Stock Analysis Dashboard

可视化股票分析仪表盘，支持多市场数据展示与技术/基本面分析。

## 功能特性

- **价格走势图** — K线图（OHLCV），支持 1M / 3M / 6M / 1Y / 3Y 周期切换
- **技术指标** — MA5/10/20/60、MACD、RSI（14日）、布林带，叠加在同一图表
- **基本面数据** — PE、PB、营收/净利润、股息率、总市值
- **资金流向** — 北向资金（A股）、主力净流入、龙虎榜
- **自选股管理** — 侧边栏增删自选股，默认纳斯达克 100 前 20 只
- **实时价格** — WebSocket 实时推送当前查看股票的最新价格

## 支持市场

| 市场 | 数据源 |
|------|--------|
| A股（沪深） | akshare |
| 港股 | akshare |
| 美股（NYSE/NASDAQ） | yfinance |
| ETF / 基金 | akshare / yfinance |

## Tech Stack

- **Frontend**: React 19 + Vite + TypeScript + Tailwind CSS + TradingView Lightweight Charts v5
- **Backend**: Python 3.13 + FastAPI + SQLAlchemy 2.x async
- **Data**: akshare, yfinance

## 前置条件

- [Anaconda / Miniconda](https://docs.conda.io/en/latest/) 已安装
- conda base 环境中包含 Python 3.13 和 Node.js（v20+）

确认方式：

```bash
conda run -n base python --version   # Python 3.13.x
conda run -n base node --version     # v20.x.x
```

## 快速开始

### 1. 安装依赖

```bash
# 后端依赖
cd backend
conda run -n base pip install -r requirements.txt

# 前端依赖
cd ../frontend
conda run -n base npm install
```

### 2. 启动服务（需要两个终端）

**终端 1 — 启动后端**

```bash
cd backend
conda run -n base uvicorn main:app --reload --port 8000
```

看到以下输出表示启动成功：

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
```

**终端 2 — 启动前端**

```bash
cd frontend
conda run -n base npm run dev
```

看到以下输出表示启动成功：

```
VITE v7.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

### 3. 打开浏览器

访问 **http://localhost:5173**

> **注意**：必须先启动后端（端口 8000），前端才能正常加载数据。前端通过 Vite 代理将 `/api` 和 `/ws` 请求转发到后端。

## 页面说明

```
┌─────────────────────────────────────────────────────────┐
│  顶部栏：搜索框 + 当前股票代码 + 实时价格/涨跌幅       │
├────────────┬────────────────────────────────────────────┤
│            │  K线图 + 技术指标叠加                      │
│  自选股     │  工具栏：股票名称 | 周期切换 | 指标开关    │
│  侧边栏     ├────────────────────────────────────────────┤
│            │  基本面面板       │  资金流向面板            │
│            │  PE/PB/市值/营收  │  北向/主力/龙虎榜       │
└────────────┴────────────────────────────────────────────┘
```

- **左侧侧边栏**：点击切换股票，✕ 删除自选股
- **图表区域**：切换周期（1M/3M/6M/1Y/3Y），开关指标（MA/MACD/RSI/BOLLINGER）
- **底部面板**：自动加载当前股票的基本面和资金流向数据

## 开发命令

```bash
# 后端测试（62 个测试）
cd backend && conda run -n base pytest

# 前端类型检查
cd frontend && conda run -n base npm run typecheck

# 前端测试
cd frontend && conda run -n base npm run test:run

# 前端构建
cd frontend && conda run -n base npm run build
```

## API 文档

启动后端后，访问 **http://localhost:8000/docs** 可查看交互式 Swagger API 文档。

主要端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stocks/{symbol}/ohlcv` | 历史 K 线 |
| GET | `/api/stocks/{symbol}/quote` | 实时报价 |
| GET | `/api/stocks/search?q=` | 搜索股票 |
| GET | `/api/indicators/{symbol}` | 技术指标 |
| GET | `/api/fundamentals/{symbol}` | 基本面 |
| GET | `/api/capital-flow/{symbol}` | 资金流向（仅 A 股） |
| GET/POST/DELETE | `/api/watchlist` | 自选股管理 |
| WS | `/ws/price/{symbol}` | 实时价格推送 |

## 项目结构

```
stock_analysis/
├── backend/
│   ├── main.py               # FastAPI 入口
│   ├── config.py              # 环境变量配置
│   ├── database.py            # 数据库连接
│   ├── models/
│   │   ├── watchlist.py       # 自选股模型
│   │   ├── ohlcv.py           # OHLCV K线缓存模型
│   │   └── fundamentals.py    # 基本面缓存模型
│   ├── schemas/               # Pydantic 请求/响应模型
│   ├── routers/               # API 路由（stocks/indicators/fundamentals/...）
│   ├── services/
│   │   ├── fetcher.py         # 数据源适配（akshare/yfinance）
│   │   ├── stock_data.py      # OHLCV 本地缓存 + 增量拉取
│   │   ├── fundamentals_data.py # 基本面本地缓存（每日刷新）
│   │   ├── calculator.py      # 技术指标计算
│   │   └── cache.py           # TTL 内存缓存
│   └── tests/                 # pytest 测试
├── frontend/
│   ├── src/
│   │   ├── components/        # React 组件
│   │   ├── hooks/             # 自定义 hooks（WebSocket/Watchlist）
│   │   ├── api/               # API 客户端封装
│   │   └── types/             # TypeScript 类型定义
│   └── package.json
└── docs/
    └── frontend-ux.md         # 前端交互设计文档
```

## 环境变量

在 `backend/` 目录下创建 `.env`（可选）：

```env
TUSHARE_TOKEN=   # 可选，用于获取更丰富的 A 股数据
```
