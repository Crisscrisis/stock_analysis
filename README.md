# Stock Analysis Dashboard

可视化股票分析仪表盘，支持多市场数据展示与技术/基本面分析。

## 功能特性

- **价格走势图** — K线图（OHLCV），支持 1M / 3M / 6M / 1Y / 3Y 周期切换
- **技术指标** — MA5/10/20/60、MACD、RSI（14日）、布林带，叠加在同一图表
- **基本面数据** — PE、PB、营收/净利润、股息率、总市值
- **资金流向** — 北向资金（A股）、主力净流入、龙虎榜
- **多市场搜索** — 支持 A股/美股/港股 统一搜索，结果带市场标记，回车快速选股
- **自选股管理** — 侧边栏增删自选股，显示市场标记（A/US/HK），默认纳斯达克 100 前 20 只
- **实时价格** — WebSocket 实时推送当前查看股票的最新价格
- **指数成分股采集** — 自动采集纳斯达克100、恒生指数、恒生科技指数全部成分股数据（OHLCV、基本面、财报、分红），支持定时采集与手动触发

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

## CLI 数据查看工具

项目提供了一个只读 CLI 工具，可直接查看本地 SQLite 数据库中的缓存数据，无需启动后端服务。

```bash
cd backend

# 数据库概览（文件大小、各表行数、数据时间范围）
python cli.py stats

# 查看自选股列表
python cli.py watchlist

# 列出所有有缓存数据的股票及 K 线条数
python cli.py ohlcv --list

# 查看某只股票的 OHLCV 数据（默认最近 20 条）
python cli.py ohlcv AAPL

# 指定条数和周期
python cli.py ohlcv AAPL --limit 50
python cli.py ohlcv AAPL --interval 1w

# 查看所有缓存的基本面数据
python cli.py fundamentals

# 查看某只股票的基本面详情
python cli.py fundamentals AAPL

# 指定数据库路径（默认 ./stock_analysis.db）
python cli.py --db /path/to/other.db stats
```

> **注意**：以上查看命令为纯只读操作，不会修改任何数据。

## 指数成分股采集器

采集器会自动获取纳斯达克100、恒生指数、恒生科技指数的全部成分股，并采集每只股票的 OHLCV K线、基本面、财报摘要、分红记录。

### 覆盖指数

| 指数 | 市场 | 成分股数 | 数据源 |
|------|------|---------|--------|
| NASDAQ100 | 美股 | ~100 只 | yfinance |
| HSI（恒生指数） | 港股 | ~80 只 | akshare |
| HSTECH（恒生科技） | 港股 | ~30 只 | akshare |

### 手动采集

```bash
cd backend

# 采集全部三个指数
python cli.py crawl

# 只采集某个指数
python cli.py crawl NASDAQ100
python cli.py crawl HSI
python cli.py crawl HSTECH

# 强制回补近 1 年历史数据（首次使用或需要补数据时）
python cli.py crawl --backfill
python cli.py crawl NASDAQ100 --backfill
```

每次采集完成后会输出汇总报告：

```
=== NASDAQ100 采集报告 ===
耗时:   4m 32s
成分股: 100 总计 | 97 成功 | 2 失败 | 1 跳过(去重)
调仓:   +0 新增, -0 移出
===============================
```

### 定时采集

启动后端服务后，采集器会按以下时间自动运行（无需额外操作）：

| 任务 | 触发时间 (UTC) | 说明 |
|------|---------------|------|
| 港股（HSI + HSTECH） | 周一至周五 08:30 | 港股 16:30 HKT 收盘后 |
| 美股（NASDAQ100） | 周一至周五 22:00 | 美股 17:00 ET 收盘后 |

```bash
# 启动后端（同时启动定时采集）
cd backend
conda run -n base uvicorn main:app --reload --port 8000
```

日志中会显示 scheduler 启动信息，确认定时任务已注册。

### 采集行为说明

- **增量采集**：已有数据的股票只拉取最近 1 个月增量；无数据的股票自动回补 1 年
- **幂等写入**：重复运行不会产生重复数据（ON CONFLICT DO NOTHING）
- **失败隔离**：单只股票采集失败不影响其他股票，失败列表会在报告中列出
- **跨指数去重**：恒生指数和恒生科技指数的重叠成分股只请求一次数据源
- **成分股调仓**：自动检测成分股变化，新增股票开始采集，移出股票标记为非活跃（历史数据保留）

## 开发命令

```bash
# 后端测试（159 个测试）
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
| GET | `/api/stocks/search?q=` | 搜索股票（A/US/HK 多市场） |
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
│   ├── cli.py                # CLI 数据查看工具（只读）
│   ├── config.py              # 环境变量配置
│   ├── database.py            # 数据库连接
│   ├── models/
│   │   ├── watchlist.py       # 自选股模型
│   │   ├── ohlcv.py           # OHLCV K线缓存模型
│   │   ├── fundamentals.py    # 基本面缓存模型
│   │   ├── index_constituent.py # 指数成分股模型
│   │   ├── earnings.py        # 财报摘要模型
│   │   └── dividend.py        # 分红记录模型
│   ├── schemas/               # Pydantic 请求/响应模型
│   ├── routers/               # API 路由（stocks/indicators/fundamentals/...）
│   ├── services/
│   │   ├── fetcher.py         # 数据源适配（akshare/yfinance）
│   │   ├── stock_data.py      # OHLCV 本地缓存 + 增量拉取
│   │   ├── fundamentals_data.py # 基本面本地缓存（每日刷新）
│   │   ├── calculator.py      # 技术指标计算
│   │   └── cache.py           # TTL 内存缓存
│   ├── crawler/               # 指数成分股采集器
│   │   ├── registry.py        # 指数注册表（名称、市场、调度时间）
│   │   ├── constituents.py    # 成分股列表获取（Wikipedia/akshare）
│   │   ├── collectors.py      # 单只股票数据采集
│   │   ├── orchestrator.py    # 编排：并发控制、去重、报告
│   │   ├── report.py          # 采集报告数据结构
│   │   └── scheduler.py       # APScheduler 定时任务
│   └── tests/                 # pytest 测试
├── frontend/
│   ├── src/
│   │   ├── components/        # React 组件
│   │   ├── hooks/             # 自定义 hooks（WebSocket/Watchlist）
│   │   ├── api/               # API 客户端封装
│   │   └── types/             # TypeScript 类型定义
│   └── package.json
└── docs/
    ├── frontend-ux.md         # 前端交互设计文档
    ├── spec_web_crawler.md    # 采集器产品需求规格
    ├── plan_web_crawler.md    # 采集器技术实现计划
    └── task_web_crawler.md    # 采集器原子任务列表
```

## 环境变量

在 `backend/` 目录下创建 `.env`（可选）：

```env
TUSHARE_TOKEN=   # 可选，用于获取更丰富的 A 股数据
```
