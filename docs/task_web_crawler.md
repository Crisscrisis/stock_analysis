# 指数成分股数据采集器 — 原子任务列表

> 基于 [plan_web_crawler.md](./plan_web_crawler.md)
> 规则：每个任务只改 **一个文件**，测试先行（先写测试，再写实现）

---

## Phase 1: 数据模型

### T-01: IndexConstituent 模型测试

- **文件**: `tests/test_crawler_models.py`（新建）
- **内容**: 测试 IndexConstituent 表创建、插入、唯一约束 `(index_name, symbol)`、is_active 默认值、removed_at 可为空
- **依赖**: 无
- **对应 US**: US-1, US-7

### T-02: IndexConstituent 模型实现

- **文件**: `models/index_constituent.py`（新建）
- **内容**: IndexConstituent ORM 模型，字段见 plan §2.1
- **依赖**: T-01
- **验证**: `pytest tests/test_crawler_models.py` 中 IndexConstituent 相关测试通过

### T-03: Earnings 模型测试

- **文件**: `tests/test_crawler_models.py`（追加）
- **内容**: 测试 Earnings 表创建、插入、唯一约束 `(symbol, period_end, period_type)`、可空字段
- **依赖**: T-01
- **对应 US**: US-1

### T-04: Earnings 模型实现

- **文件**: `models/earnings.py`（新建）
- **内容**: Earnings ORM 模型，字段见 plan §2.2
- **依赖**: T-03
- **验证**: `pytest tests/test_crawler_models.py` 中 Earnings 相关测试通过

### T-05: Dividend 模型测试

- **文件**: `tests/test_crawler_models.py`（追加）
- **内容**: 测试 Dividend 表创建、插入、唯一约束 `(symbol, ex_date)`、currency 默认值
- **依赖**: T-01
- **对应 US**: US-1

### T-06: Dividend 模型实现

- **文件**: `models/dividend.py`（新建）
- **内容**: Dividend ORM 模型，字段见 plan §2.3
- **依赖**: T-05
- **验证**: `pytest tests/test_crawler_models.py` 中 Dividend 相关测试通过

### T-07: models/__init__.py 导出新模型

- **文件**: `models/__init__.py`（修改）
- **内容**: 添加 `from .index_constituent import IndexConstituent`、`from .earnings import Earnings`、`from .dividend import Dividend`
- **依赖**: T-02, T-04, T-06
- **验证**: `pytest` 全量通过（现有 87 个测试不受影响）

---

## Phase 2: 采集报告（纯数据结构，无外部依赖）

### T-08: CollectionReport 测试

- **文件**: `tests/test_crawler_report.py`（新建）
- **内容**: 测试 StockResult 和 CollectionReport 数据结构创建、print_summary() 输出格式（含成功/失败/跳过/调仓统计、耗时格式化、失败列表）
- **依赖**: 无
- **对应 US**: US-5

### T-09: CollectionReport 实现

- **文件**: `crawler/report.py`（新建，同时新建 `crawler/__init__.py`）
- **内容**: StockResult、CollectionReport 数据类，print_summary() 方法
- **依赖**: T-08
- **验证**: `pytest tests/test_crawler_report.py` 通过

---

## Phase 3: 指数注册表与成分股获取

### T-10: 指数注册表测试

- **文件**: `tests/test_crawler_constituents.py`（新建）
- **内容**: 测试 IndexConfig 数据结构、INDICES 字典包含 NASDAQ100/HSI/HSTECH 三个键、get_index() 查找、all_indices() 返回列表、未知指数报错
- **依赖**: 无
- **对应 US**: US-1

### T-11: 指数注册表实现

- **文件**: `crawler/registry.py`（新建）
- **内容**: IndexConfig dataclass、INDICES 字典、get_index()、all_indices()；fetch_constituents 字段暂指向占位函数
- **依赖**: T-10
- **验证**: `pytest tests/test_crawler_constituents.py` 中 registry 相关测试通过

### T-12: NASDAQ-100 成分股获取测试

- **文件**: `tests/test_crawler_constituents.py`（追加）
- **内容**: mock `pd.read_html` 返回 Wikipedia 页面的 DataFrame，验证 fetch_nasdaq100() 返回正确格式 `[{"symbol": "AAPL", "name": "Apple Inc."}, ...]`、symbol 无前缀后缀、异常时 fallback 行为
- **依赖**: T-10
- **对应 US**: US-1

### T-13: NASDAQ-100 成分股获取实现

- **文件**: `crawler/constituents.py`（新建）
- **内容**: `fetch_nasdaq100()` — 通过 `asyncio.to_thread()` 调用 `pd.read_html(Wikipedia_URL)` 解析成分股列表
- **依赖**: T-12
- **验证**: `pytest tests/test_crawler_constituents.py` 中 nasdaq100 相关测试通过

### T-14: HSI / HSTECH 成分股获取测试

- **文件**: `tests/test_crawler_constituents.py`（追加）
- **内容**: mock akshare 函数，验证 fetch_hsi() 和 fetch_hstech() 返回正确格式、symbol 带 `.HK` 后缀、异常时 fallback 行为
- **依赖**: T-10
- **对应 US**: US-1

### T-15: HSI / HSTECH 成分股获取实现

- **文件**: `crawler/constituents.py`（修改）
- **内容**: `fetch_hsi()`、`fetch_hstech()` — 通过 akshare 获取恒生指数和恒生科技指数成分股
- **依赖**: T-14
- **验证**: `pytest tests/test_crawler_constituents.py` 中 hsi/hstech 相关测试通过

### T-16: 注册表接入真实获取函数

- **文件**: `crawler/registry.py`（修改）
- **内容**: 将 INDICES 中三个指数的 `fetch_constituents` 从占位函数替换为 constituents.py 中的真实函数
- **依赖**: T-13, T-15
- **验证**: `pytest tests/test_crawler_constituents.py` 全量通过

---

## Phase 4: fetcher 扩展

### T-17: 财报获取测试

- **文件**: `tests/test_fetcher_extras.py`（新建）
- **内容**: mock yfinance `Ticker().quarterly_income_stmt` 和 `Ticker().income_stmt`，验证 `get_earnings()` 返回 `[{"period_end": "...", "period_type": "quarterly", "revenue": ..., ...}]`；mock akshare 对应函数验证 HK 路径
- **依赖**: 无
- **对应 US**: US-1

### T-18: 财报获取实现

- **文件**: `services/fetcher.py`（修改）
- **内容**: 新增 `_sync_earnings_yfinance()`、`_sync_earnings_akshare_hk()`、`async get_earnings()`
- **依赖**: T-17
- **验证**: `pytest tests/test_fetcher_extras.py` 中 earnings 测试通过

### T-19: 分红获取测试

- **文件**: `tests/test_fetcher_extras.py`（追加）
- **内容**: mock yfinance `Ticker().dividends`，验证 `get_dividends()` 返回 `[{"ex_date": "...", "amount": ..., "currency": "USD"}]`；mock akshare 对应函数验证 HK 路径
- **依赖**: T-17
- **对应 US**: US-1

### T-20: 分红获取实现

- **文件**: `services/fetcher.py`（修改）
- **内容**: 新增 `_sync_dividends_yfinance()`、`_sync_dividends_akshare_hk()`、`async get_dividends()`
- **依赖**: T-19
- **验证**: `pytest tests/test_fetcher_extras.py` 中 dividends 测试通过

### T-21: 港股基本面获取测试

- **文件**: `tests/test_fetcher_extras.py`（追加）
- **内容**: mock akshare 港股估值函数，验证 `get_fundamentals("00700.HK")` 返回完整字段而非全 None
- **依赖**: T-17

### T-22: 港股基本面获取实现

- **文件**: `services/fetcher.py`（修改）
- **内容**: 新增 `_sync_fundamentals_akshare_hk()`，修改 `get_fundamentals()` 的 HK 分支调用新函数
- **依赖**: T-21
- **验证**: `pytest tests/test_fetcher_extras.py` 中 HK fundamentals 测试通过

---

## Phase 5: 数据采集器（collectors）

### T-23: collect_ohlcv 测试

- **文件**: `tests/test_crawler_collectors.py`（新建）
- **内容**: mock `fetcher.get_ohlcv`，测试增量采集（DB 有数据）和回补采集（DB 无数据/backfill=True 使用 period="1Y"），验证数据写入 ohlcv_bar 表、on_conflict 去重
- **依赖**: T-02
- **对应 US**: US-1, US-4

### T-24: collect_ohlcv 实现

- **文件**: `crawler/collectors.py`（新建）
- **内容**: `collect_ohlcv(db, symbol, market, backfill)` — 复用现有 stock_data 的 upsert 模式
- **依赖**: T-23
- **验证**: `pytest tests/test_crawler_collectors.py` 中 ohlcv 测试通过

### T-25: collect_fundamentals 测试

- **文件**: `tests/test_crawler_collectors.py`（追加）
- **内容**: mock `fetcher.get_fundamentals`，测试数据写入 fundamentals_cache 表、更新已有记录
- **依赖**: T-23

### T-26: collect_fundamentals 实现

- **文件**: `crawler/collectors.py`（修改）
- **内容**: `collect_fundamentals(db, symbol, market)` — 复用现有 fundamentals_data 的 upsert 模式
- **依赖**: T-25
- **验证**: `pytest tests/test_crawler_collectors.py` 中 fundamentals 测试通过

### T-27: collect_earnings 测试

- **文件**: `tests/test_crawler_collectors.py`（追加）
- **内容**: mock `fetcher.get_earnings`，测试数据写入 earnings 表、唯一约束去重、空数据时返回 True（跳过而非失败）
- **依赖**: T-04, T-23

### T-28: collect_earnings 实现

- **文件**: `crawler/collectors.py`（修改）
- **内容**: `collect_earnings(db, symbol, market)`
- **依赖**: T-27
- **验证**: `pytest tests/test_crawler_collectors.py` 中 earnings 测试通过

### T-29: collect_dividends 测试

- **文件**: `tests/test_crawler_collectors.py`（追加）
- **内容**: mock `fetcher.get_dividends`，测试数据写入 dividend 表、唯一约束去重
- **依赖**: T-06, T-23

### T-30: collect_dividends 实现

- **文件**: `crawler/collectors.py`（修改）
- **内容**: `collect_dividends(db, symbol, market)`
- **依赖**: T-29
- **验证**: `pytest tests/test_crawler_collectors.py` 中 dividends 测试通过

### T-31: collect_all_for_stock 测试

- **文件**: `tests/test_crawler_collectors.py`（追加）
- **内容**: mock 各 collect_* 函数，测试 `collect_all_for_stock()` 返回 `{"ohlcv": True, "fundamentals": True, ...}`、单个 collector 异常不影响其他 collector
- **依赖**: T-23
- **对应 US**: US-6

### T-32: collect_all_for_stock 实现

- **文件**: `crawler/collectors.py`（修改）
- **内容**: `collect_all_for_stock(db, symbol, market, backfill)` — 调用各 collect_* 并捕获异常
- **依赖**: T-31
- **验证**: `pytest tests/test_crawler_collectors.py` 全量通过

---

## Phase 6: 编排器（orchestrator）

### T-33: _reconcile_constituents 测试

- **文件**: `tests/test_crawler_orchestrator.py`（新建）
- **内容**: 测试成分股对账逻辑：
  - 全新指数 → 所有成分股标记为 active
  - 已有成分股不变 → 无变化
  - 新增成分股 → 插入 active 记录
  - 移出成分股 → is_active=False + removed_at 设值
  - 已移出后重新加入 → is_active 恢复为 True + removed_at 清空
- **依赖**: T-02
- **对应 US**: US-7

### T-34: _reconcile_constituents 实现

- **文件**: `crawler/orchestrator.py`（新建）
- **内容**: `_reconcile_constituents(db, index_name, market, fresh_list)` → `(added, removed)`
- **依赖**: T-33
- **验证**: `pytest tests/test_crawler_orchestrator.py` 中 reconcile 测试通过

### T-35: crawl_index 测试

- **文件**: `tests/test_crawler_orchestrator.py`（追加）
- **内容**: mock registry + collectors，测试：
  - 正常流程 → 返回 CollectionReport（total/succeeded/failed 计数正确）
  - already_collected 去重 → skipped 计数正确
  - 成分股数量异常 → 使用上次 DB 列表 + 记录警告
  - 成分股列表获取失败 → fallback 到 DB 列表
  - Semaphore 限制并发（验证同时运行不超过 5 个）
- **依赖**: T-08, T-33
- **对应 US**: US-1, US-5, US-6

### T-36: crawl_index 实现

- **文件**: `crawler/orchestrator.py`（修改）
- **内容**: `crawl_index(session_factory, index_name, already_collected)` → CollectionReport
- **依赖**: T-35
- **验证**: `pytest tests/test_crawler_orchestrator.py` 中 crawl_index 测试通过

### T-37: crawl_all 测试

- **文件**: `tests/test_crawler_orchestrator.py`（追加）
- **内容**: mock crawl_index，测试：
  - 按顺序调用三个指数
  - collected set 在指数间传递（跨指数去重）
  - 返回 3 个 CollectionReport
- **依赖**: T-35
- **对应 US**: US-1

### T-38: crawl_all 实现

- **文件**: `crawler/orchestrator.py`（修改）
- **内容**: `crawl_all(session_factory)` → `list[CollectionReport]`
- **依赖**: T-37
- **验证**: `pytest tests/test_crawler_orchestrator.py` 全量通过

---

## Phase 7: CLI 集成

### T-39: CLI crawl 子命令测试

- **文件**: `tests/test_cli.py`（追加）
- **内容**: mock `crawler.orchestrator.crawl_index` 和 `crawl_all`，测试：
  - `cli.py crawl` → 调用 crawl_all
  - `cli.py crawl NASDAQ100` → 调用 crawl_index("NASDAQ100")
  - `cli.py crawl --backfill` → backfill 参数传递
  - 无效指数名 → 错误提示
- **依赖**: T-36
- **对应 US**: US-3

### T-40: CLI crawl 子命令实现

- **文件**: `cli.py`（修改）
- **内容**: 新增 `crawl` 子命令解析器 + `cmd_crawl()` 函数（通过 `asyncio.run()` 桥接异步调用）
- **依赖**: T-39
- **验证**: `pytest tests/test_cli.py` 全量通过

---

## Phase 8: APScheduler 集成

### T-41: scheduler 测试

- **文件**: `tests/test_crawler_scheduler.py`（新建）
- **内容**: 测试：
  - `init_scheduler()` 返回 AsyncIOScheduler 实例
  - 注册了 3 个 cron job（HSI/HSTECH 共享一个 HK job + NASDAQ100 一个 US job，或各自独立）
  - job 的 cron 表达式正确（小时、分钟、day_of_week=mon-fri）
  - `shutdown_scheduler()` 可正常关闭
- **依赖**: T-36
- **对应 US**: US-2

### T-42: scheduler 实现

- **文件**: `crawler/scheduler.py`（新建）
- **内容**: `init_scheduler()`、`start_scheduler()`、`shutdown_scheduler()`
- **依赖**: T-41
- **验证**: `pytest tests/test_crawler_scheduler.py` 通过

### T-43: main.py lifespan 集成

- **文件**: `main.py`（修改）
- **内容**: lifespan 中调用 `start_scheduler(AsyncSessionLocal)` / `shutdown_scheduler()`
- **依赖**: T-42
- **验证**: `uvicorn main:app` 启动无报错，日志中可见 scheduler 启动信息

---

## Phase 9: 依赖与包初始化

### T-44: requirements.txt 更新

- **文件**: `requirements.txt`（修改）
- **内容**: 新增 `apscheduler>=3.10.0`、`beautifulsoup4>=4.12.0`、`lxml>=5.0.0`
- **依赖**: 无（可在 Phase 1 之前或任意时刻执行）
- **验证**: `conda run -n base pip install -r requirements.txt` 成功

### T-45: crawler 包初始化

- **文件**: `crawler/__init__.py`（新建）
- **内容**: 空文件或简单导出 `from .orchestrator import crawl_index, crawl_all`
- **依赖**: T-38
- **验证**: `from crawler import crawl_index, crawl_all` 不报错

---

## Phase 10: 端到端验证

### T-46: 全量测试回归

- **文件**: 无（只运行测试）
- **内容**: `conda run -n base pytest` — 全部测试通过，无回归
- **依赖**: T-01 ~ T-45

### T-47: 手动采集冒烟测试

- **文件**: 无（只运行命令）
- **内容**:
  ```bash
  conda run -n base python cli.py crawl NASDAQ100
  conda run -n base python cli.py stats
  conda run -n base python cli.py ohlcv --list
  ```
- **依赖**: T-46

### T-48: 定时任务冒烟测试

- **文件**: 无（只运行命令）
- **内容**: 启动 `uvicorn main:app --port 8000`，确认日志中出现 scheduler 启动和 job 注册信息
- **依赖**: T-46

---

## 依赖关系总览

```
T-44 (requirements.txt)   可随时执行，建议最先

Phase 1 — 数据模型
T-01 → T-02 ─┐
T-03 → T-04 ─┼→ T-07 (models/__init__.py)
T-05 → T-06 ─┘

Phase 2 — 采集报告
T-08 → T-09

Phase 3 — 注册表 & 成分股
T-10 → T-11 ─────────────────→ T-16 (接入真实函数)
T-12 → T-13 (NASDAQ100) ─────→ T-16
T-14 → T-15 (HSI/HSTECH) ────→ T-16

Phase 4 — fetcher 扩展
T-17 → T-18 (earnings)
T-19 → T-20 (dividends)
T-21 → T-22 (HK fundamentals)

Phase 5 — collectors
T-23 → T-24 (ohlcv)
T-25 → T-26 (fundamentals)
T-27 → T-28 (earnings)        需 T-04
T-29 → T-30 (dividends)       需 T-06
T-31 → T-32 (all_for_stock)

Phase 6 — orchestrator
T-33 → T-34 (reconcile)       需 T-02
T-35 → T-36 (crawl_index)     需 T-09, T-34
T-37 → T-38 (crawl_all)       需 T-36

Phase 7 — CLI
T-39 → T-40                   需 T-36

Phase 8 — scheduler
T-41 → T-42 → T-43            需 T-36

Phase 9 — 包初始化
T-45                           需 T-38

Phase 10 — 端到端
T-46 → T-47 → T-48
```

## 并行执行建议

以下任务组之间无依赖，可同时进行：

| 并行组 | 任务 |
|--------|------|
| A | Phase 1 (T-01~T-07) |
| B | Phase 2 (T-08~T-09) |
| C | Phase 3 (T-10~T-16) |
| D | Phase 4 (T-17~T-22) |

Phase 5 (T-23~T-32) 依赖 A + D 完成后开始。
Phase 6 (T-33~T-38) 依赖 A + B + Phase 5 完成后开始。
Phase 7~9 依赖 Phase 6 完成后可并行。
