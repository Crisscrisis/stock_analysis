import os

# 代理策略:
#   akshare → 东方财富(eastmoney.com) 是国内站，必须绕过代理直连
#   yfinance → Yahoo Finance 是海外站，需要走代理（默认行为，无需额外配置）
# 当 akshare 源不可用时，fetcher 会自动 fallback 到 yfinance
_no_proxy = os.environ.get("no_proxy", "")
if ".eastmoney.com" not in _no_proxy:
    os.environ["no_proxy"] = f"{_no_proxy},.eastmoney.com" if _no_proxy else ".eastmoney.com"

from crawler.orchestrator import crawl_all, crawl_index  # noqa: F401
