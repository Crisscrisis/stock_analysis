# 指数成分股数据采集器 — 技术实现计划

> 基于 [spec_web_crawler.md](./spec_web_crawler.md) 产品需求规格

## 技术选型摘要

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 调度器 | APScheduler 3.x | 嵌入 FastAPI 进程，原生支持 cron + 时区，无需外部服务 |
| 运行方式 | 两者兼备 | 核心逻辑独立模块，APScheduler 定时调用 + CLI 手动触发 |
| 数据库 | 同一 SQLite | stock_analysis.db 内新增表，保持简单 |
| 并发策略 | asyncio.Semaphore(5) | 同时采集 5 只股票，兼顾速度与限流风险 |
| 新增依赖 | apscheduler, beautifulsoup4, lxml | bs4+lxml 用于解析 Wikipedia 页面获取 NASDAQ-100 成分股 |

---

## 1. 目录结构

### 新增文件

```
backend/
├── crawler/                         # 采集器包
│   ├── __init__.py                  # 导出 run_crawl()
│   ├── registry.py                  # 指数注册表（名称、市场、调度时间、成分股获取函数）
│   ├── constituents.py              # 成分股列表获取（Wikipedia / akshare）
│   ├── collectors.py                # 单只股票数据采集（OHLCV / 基本面 / 财报 / 分红）
│   ├── orchestrator.py              # 主调度：遍历成分股、并发控制、去重、生成报告
│   ├── report.py                    # 采集报告数据结构与终端输出
│   └── scheduler.py                 # APScheduler 定时任务配置
├── models/
│   ├── index_constituent.py         # 成分股模型（含 is_active 状态）
│   ├── earnings.py                  # 财报摘要模型
│   └── dividend.py                  # 分红记录模型
└── tests/
    ├── test_crawler_constituents.py # 成分股获取测试
    ├── test_crawler_collectors.py   # 数据采集测试
    ├── test_crawler_orchestrator.py # 调度逻辑测试
    └── test_crawler_report.py       # 报告格式测试
```

### 需修改的现有文件

| 文件 | 改动内容 |
|------|---------|
| `models/__init__.py` | 导出 IndexConstituent, Earnings, Dividend |
| `main.py` | lifespan 中启动/关闭 APScheduler |
| `cli.py` | 新增 `crawl` 子命令 |
| `services/fetcher.py` | 新增财报、分红、港股基本面获取函数 |
| `requirements.txt` | 新增 apscheduler, beautifulsoup4, lxml |

---

## 2. 核心数据模型

### 2.1 IndexConstituent（成分股）

```
表名: index_constituent
唯一约束: (index_name, symbol)
索引: index_name, is_active
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| index_name | String(50) | 指数名称: NASDAQ100 / HSI / HSTECH |
| symbol | String(20) | 股票代码: AAPL / 00700.HK |
| name | String(100)? | 股票名称 |
| market | String(10) | 市场: US / HK |
| is_active | Boolean | 是否为当前成分股（调仓时标记为 False） |
| added_at | DateTime | 加入时间 |
| removed_at | DateTime? | 移出时间（仅 is_active=False 时有值） |

### 2.2 Earnings（财报摘要）

```
表名: earnings
唯一约束: (symbol, period_end, period_type)
索引: symbol
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| symbol | String(20) | 股票代码 |
| period_end | String(10) | 报告期末日: "2025-03-31" |
| period_type | String(10) | "quarterly" 或 "annual" |
| revenue | Float? | 营收 |
| net_income | Float? | 净利润 |
| eps | Float? | 每股收益 |
| gross_profit | Float? | 毛利润 |
| operating_income | Float? | 营业利润 |
| updated_ts | Integer | 更新时间戳 |

### 2.3 Dividend（分红记录）

```
表名: dividend
唯一约束: (symbol, ex_date)
索引: symbol
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| symbol | String(20) | 股票代码 |
| ex_date | String(10) | 除权除息日: "2025-02-07" |
| amount | Float | 每股分红金额 |
| currency | String(10) | 币种: USD / HKD |
| updated_ts | Integer | 更新时间戳 |

---

## 3. 接口定义

### 3.1 指数注册表 — `crawler/registry.py`

```python
@dataclass(frozen=True)
class IndexConfig:
    name: str                    # "NASDAQ100" | "HSI" | "HSTECH"
    market: str                  # "US" | "HK"
    expected_count: tuple[int, int]  # 成分股数量合理范围，用于异常检测
    cron_hour: int               # UTC 调度小时
    cron_minute: int             # UTC 调度分钟
    fetch_constituents: Callable  # 指向 constituents.py 中的获取函数

INDICES: dict[str, IndexConfig]  # 预注册的三个指数
```

> 扩展新指数只需：1) 写一个 `fetch_xxx()` 函数  2) 在 INDICES 中添加一条注册

### 3.2 成分股获取 — `crawler/constituents.py`

```python
async def fetch_nasdaq100() -> list[dict[str, str]]
    # Wikipedia pd.read_html() 解析 NASDAQ-100 页面
    # 返回 [{"symbol": "AAPL", "name": "Apple Inc."}, ...]

async def fetch_hsi() -> list[dict[str, str]]
    # akshare 获取恒生指数成分股

async def fetch_hstech() -> list[dict[str, str]]
    # akshare 获取恒生科技指数成分股
```

### 3.3 数据采集 — `crawler/collectors.py`

```python
async def collect_ohlcv(db, symbol, market, backfill=False) -> bool
async def collect_fundamentals(db, symbol, market) -> bool
async def collect_earnings(db, symbol, market) -> bool
async def collect_dividends(db, symbol, market) -> bool
async def collect_all_for_stock(db, symbol, market, backfill=False) -> dict[str, bool]
    # 返回 {"ohlcv": True, "fundamentals": True, "earnings": False, ...}
```

### 3.4 调度编排 — `crawler/orchestrator.py`

```python
async def crawl_index(
    session_factory,
    index_name: str,
    already_collected: set[str] | None = None,  # 跨指数去重
) -> CollectionReport

async def crawl_all(session_factory) -> list[CollectionReport]
    # 按顺序采集所有指数，维护 collected set 去重
```

**编排流程：**
1. 通过 registry 获取成分股列表
2. 数量异常检测（偏离 expected_count 过大时使用上次 DB 中的列表）
3. 与 DB 对账：新增 → 插入并标记 active；移出 → 标记 inactive + removed_at
4. 遍历 active 成分股，Semaphore(5) 控制并发
5. 跳过 already_collected 中的 symbol（跨指数去重）
6. 对每只股票调用 `collect_all_for_stock()`，记录成功/失败
7. 生成 CollectionReport

### 3.5 采集报告 — `crawler/report.py`

```python
@dataclass
class StockResult:
    symbol: str
    success: dict[str, bool]     # 各数据类型的成功/失败
    error_message: str | None

@dataclass
class CollectionReport:
    index_name: str
    total: int
    succeeded: int
    failed: int
    skipped: int                 # 去重跳过的
    added: list[str]             # 新增成分股
    removed: list[str]           # 移出成分股
    failures: list[StockResult]
    elapsed_seconds: float

    def print_summary(self) -> None
```

**报告输出示例：**

```
=== NASDAQ100 采集报告 ===
耗时:   4m 32s
成分股: 100 总计 | 97 成功 | 2 失败 | 1 跳过(去重)
调仓:   +0 新增, -0 移出
失败列表:
  SMCI  ohlcv=OK  fundamentals=FAIL(timeout)  earnings=OK  dividends=OK
  MRVL  ohlcv=FAIL(no data)  fundamentals=OK  earnings=OK  dividends=OK
===============================
```

### 3.6 定时调度 — `crawler/scheduler.py`

```python
def init_scheduler(session_factory) -> AsyncIOScheduler
async def start_scheduler(session_factory) -> None
async def shutdown_scheduler() -> None
```

**调度计划（UTC）：**

| 任务 | cron 表达式 | 说明 |
|------|------------|------|
| HSI + HSTECH | `hour=8, minute=30, day_of_week=mon-fri` | 港股 16:30 HKT 收盘后 |
| NASDAQ100 | `hour=22, minute=0, day_of_week=mon-fri` | 美股 17:00 ET 收盘后 |

### 3.7 CLI 入口 — `cli.py` 新增子命令

```bash
python cli.py crawl                      # 采集全部指数
python cli.py crawl NASDAQ100            # 采集单个指数
python cli.py crawl --backfill           # 强制回补 1 年历史
```

### 3.8 fetcher.py 新增函数

```python
# 财报
def _sync_earnings_yfinance(symbol) -> list[dict]
def _sync_earnings_akshare_hk(symbol) -> list[dict]
async def get_earnings(symbol) -> list[dict]

# 分红
def _sync_dividends_yfinance(symbol) -> list[dict]
def _sync_dividends_akshare_hk(symbol) -> list[dict]
async def get_dividends(symbol) -> list[dict]

# 港股基本面（现有 get_fundamentals 的 HK 分支目前返回全 None，需实现）
def _sync_fundamentals_akshare_hk(symbol) -> dict
```

---

## 4. 关键设计决策

### 跨指数去重
恒生指数与恒生科技指数有重叠成分股（如腾讯 00700.HK）。`crawl_all()` 按顺序采集各指数，维护 `collected: set[str]`，相同 symbol 只向数据源请求一次。成分股表中两个指数各自独立记录。

### 回补检测
`collect_ohlcv()` 检查 DB 中该 symbol 是否有历史数据：
- 无数据 → 自动回补 1 年（period="1Y"）
- 有数据 → 增量采集（复用现有 `stock_data.get_ohlcv()` 逻辑）
- `--backfill` 标志 → 强制回补

### 幂等性
所有写入使用 `INSERT ... ON CONFLICT DO NOTHING`（现有 upsert 模式），同一天重复运行不会产生重复数据。

---

## 5. 实施阶段

### Phase 1: 数据模型

**交付物：** IndexConstituent / Earnings / Dividend 三个 ORM 模型 + models/__init__.py 更新

**验证：** 现有全部测试通过 + 新模型测试（建表、唯一约束、插入/查询）

---

### Phase 2: 成分股获取

**交付物：** `crawler/__init__.py`, `crawler/registry.py`, `crawler/constituents.py`

**验证：** mock 测试覆盖三个指数的成分股获取、symbol 格式正确、数量异常检测

---

### Phase 3: fetcher 扩展

**交付物：** fetcher.py 中新增 earnings / dividends / HK fundamentals 获取函数

**验证：** mock 测试覆盖 yfinance 和 akshare 两个数据源路径，返回格式一致

---

### Phase 4: 采集器与编排

**交付物：** `crawler/collectors.py`, `crawler/orchestrator.py`, `crawler/report.py`

**验证：**
- 成分股对账（新增/移出标记）
- 去重逻辑
- 失败隔离（单只失败不中断整体）
- 并发控制（Semaphore）
- 报告输出格式

---

### Phase 5: CLI 集成

**交付物：** cli.py 新增 `crawl` 子命令

**验证：** `python cli.py crawl --help` 正常，mock 下可正确调用 orchestrator

---

### Phase 6: APScheduler 集成

**交付物：** `crawler/scheduler.py` + main.py lifespan 修改 + requirements.txt 更新

**验证：** uvicorn 启动后 scheduler 正常运行，cron 任务注册正确

---

### Phase 7: 端到端验证

```bash
# 安装新依赖
cd backend && conda run -n base pip install -r requirements.txt

# 运行全部测试
conda run -n base pytest

# 手动采集（少量股票验证）
conda run -n base python cli.py crawl NASDAQ100

# 查看采集结果
conda run -n base python cli.py stats
conda run -n base python cli.py ohlcv --list

# 启动后端验证定时任务
conda run -n base uvicorn main:app --reload --port 8000
```
