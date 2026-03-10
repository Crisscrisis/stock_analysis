"""Collection report data structures and terminal output."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StockResult:
    symbol: str
    name: str
    success: dict[str, bool]
    error_message: str | None


@dataclass
class CollectionReport:
    index_name: str
    total: int
    succeeded: int
    failed: int
    skipped: int
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    failures: list[StockResult] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def _fmt_elapsed(self) -> str:
        secs = int(self.elapsed_seconds)
        if secs < 60:
            return f"{secs}s"
        minutes = secs // 60
        remaining = secs % 60
        return f"{minutes}m {remaining}s"

    def print_summary(self) -> None:
        print(f"=== {self.index_name} 采集报告 ===")
        print(f"耗时:   {self._fmt_elapsed()}")
        print(
            f"成分股: {self.total} 总计 | "
            f"{self.succeeded} 成功 | "
            f"{self.failed} 失败 | "
            f"{self.skipped} 跳过(去重)"
        )
        print(
            f"调仓:   +{len(self.added)} 新增, -{len(self.removed)} 移出"
        )
        if self.failures:
            print("失败列表:")
            for f in self.failures:
                label = f"{f.symbol} {f.name}" if f.name else f.symbol
                parts = [f"  {label} "] + [
                    f"{k}={'OK' if v else 'FAIL'}"
                    for k, v in f.success.items()
                ]
                detail = "  ".join(parts)
                if f.error_message:
                    detail += f"  ({f.error_message})"
                print(detail)
        print("=" * 31)
