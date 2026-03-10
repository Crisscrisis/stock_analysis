"""Tests for CollectionReport data structure and print_summary()."""

from crawler.report import CollectionReport, StockResult


class TestStockResult:
    def test_create(self):
        r = StockResult(
            symbol="AAPL",
            name="Apple Inc.",
            success={"ohlcv": True, "fundamentals": False},
            error_message="timeout",
        )
        assert r.symbol == "AAPL"
        assert r.name == "Apple Inc."
        assert r.success["ohlcv"] is True
        assert r.error_message == "timeout"

    def test_no_error(self):
        r = StockResult(symbol="MSFT", name="Microsoft", success={"ohlcv": True}, error_message=None)
        assert r.error_message is None


class TestCollectionReport:
    def _make_report(self, **kwargs) -> CollectionReport:
        defaults = dict(
            index_name="NASDAQ100",
            total=100,
            succeeded=97,
            failed=2,
            skipped=1,
            added=["NEW1"],
            removed=["OLD1"],
            failures=[
                StockResult("SMCI", "Super Micro", {"ohlcv": True, "fundamentals": False}, "timeout"),
                StockResult("MRVL", "Marvell", {"ohlcv": False, "fundamentals": True}, "no data"),
            ],
            elapsed_seconds=272.5,
        )
        defaults.update(kwargs)
        return CollectionReport(**defaults)

    def test_create(self):
        report = self._make_report()
        assert report.index_name == "NASDAQ100"
        assert report.total == 100
        assert report.succeeded == 97
        assert report.failed == 2
        assert report.skipped == 1

    def test_print_summary_format(self, capsys):
        report = self._make_report()
        report.print_summary()
        out = capsys.readouterr().out
        assert "NASDAQ100" in out
        assert "4m 32s" in out
        assert "97 成功" in out
        assert "2 失败" in out
        assert "1 跳过" in out
        assert "+1 新增" in out
        assert "-1 移出" in out
        assert "SMCI" in out
        assert "MRVL" in out

    def test_print_summary_no_failures(self, capsys):
        report = self._make_report(failed=0, failures=[])
        report.print_summary()
        out = capsys.readouterr().out
        assert "失败列表" not in out

    def test_elapsed_formatting_seconds(self, capsys):
        report = self._make_report(elapsed_seconds=45.0)
        report.print_summary()
        out = capsys.readouterr().out
        assert "45s" in out

    def test_elapsed_formatting_minutes(self, capsys):
        report = self._make_report(elapsed_seconds=125.0)
        report.print_summary()
        out = capsys.readouterr().out
        assert "2m 5s" in out
