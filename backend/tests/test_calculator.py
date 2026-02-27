"""Pure unit tests for services/calculator.py — no network, no DB."""
import math

import pytest

from services.calculator import calc_bollinger, calc_ma, calc_macd, calc_rsi


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _close(n: int, start: float = 100.0, step: float = 1.0) -> list[float]:
    """Ascending price series of length n."""
    return [start + i * step for i in range(n)]


# ---------------------------------------------------------------------------
# calc_ma
# ---------------------------------------------------------------------------

class TestCalcMA:
    def test_single_period(self):
        closes = _close(10)  # [100, 101, ..., 109]
        result = calc_ma(closes, [5])
        assert len(result["ma_5"]) == 10
        # First 4 values must be None (not enough data)
        assert all(v is None for v in result["ma_5"][:4])
        # 5th value = mean(100..104) = 102
        assert math.isclose(result["ma_5"][4], 102.0)

    def test_multiple_periods(self):
        closes = _close(20)
        result = calc_ma(closes, [5, 10])
        assert "ma_5" in result
        assert "ma_10" in result
        assert len(result["ma_5"]) == 20
        assert len(result["ma_10"]) == 20

    def test_period_longer_than_data(self):
        closes = _close(3)
        result = calc_ma(closes, [5])
        assert all(v is None for v in result["ma_5"])

    def test_empty_closes(self):
        result = calc_ma([], [5])
        assert result["ma_5"] == []

    def test_exact_period_length(self):
        closes = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = calc_ma(closes, [5])
        assert result["ma_5"][4] == 3.0
        assert all(v is None for v in result["ma_5"][:4])


# ---------------------------------------------------------------------------
# calc_macd
# ---------------------------------------------------------------------------

class TestCalcMACD:
    def test_output_keys(self):
        closes = _close(50)
        result = calc_macd(closes)
        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

    def test_lengths_match_input(self):
        closes = _close(50)
        result = calc_macd(closes)
        n = len(closes)
        assert len(result["macd"]) == n
        assert len(result["signal"]) == n
        assert len(result["histogram"]) == n

    def test_leading_nones(self):
        closes = _close(50)
        result = calc_macd(closes)
        # With default fast=12, slow=26, signal=9:
        # MACD line starts at index 25 (slow-1), signal at 25+8=33
        assert result["macd"][24] is None
        assert result["macd"][25] is not None

    def test_histogram_equals_macd_minus_signal(self):
        closes = _close(100)
        result = calc_macd(closes)
        for m, s, h in zip(result["macd"], result["signal"], result["histogram"]):
            if m is not None and s is not None and h is not None:
                assert math.isclose(h, m - s, abs_tol=1e-9)

    def test_short_series_all_none(self):
        closes = _close(5)
        result = calc_macd(closes)
        assert all(v is None for v in result["macd"])


# ---------------------------------------------------------------------------
# calc_rsi
# ---------------------------------------------------------------------------

class TestCalcRSI:
    def test_length_matches_input(self):
        closes = _close(30)
        result = calc_rsi(closes, 14)
        assert len(result) == 30

    def test_leading_nones(self):
        closes = _close(30)
        result = calc_rsi(closes, 14)
        # Need at least period+1 values before first RSI
        assert all(v is None for v in result[:14])
        assert result[14] is not None

    def test_rsi_bounds(self):
        closes = _close(50)
        result = calc_rsi(closes, 14)
        for v in result:
            if v is not None:
                assert 0.0 <= v <= 100.0

    def test_constant_prices_rsi(self):
        closes = [100.0] * 30
        result = calc_rsi(closes, 14)
        # No gains or losses → RSI undefined; implementation may return 50 or None
        for v in result[14:]:
            assert v is None or math.isclose(v, 50.0, abs_tol=1.0)

    def test_always_increasing(self):
        closes = _close(50, step=1.0)
        result = calc_rsi(closes, 14)
        # Continuous gains → RSI should be high (>70)
        for v in result[14:]:
            assert v is not None and v > 70.0

    def test_always_decreasing(self):
        closes = _close(50, step=-1.0)
        result = calc_rsi(closes, 14)
        for v in result[14:]:
            assert v is not None and v < 30.0


# ---------------------------------------------------------------------------
# calc_bollinger
# ---------------------------------------------------------------------------

class TestCalcBollinger:
    def test_output_keys(self):
        closes = _close(30)
        result = calc_bollinger(closes, 20)
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result

    def test_lengths(self):
        closes = _close(30)
        result = calc_bollinger(closes, 20)
        n = len(closes)
        assert len(result["upper"]) == n
        assert len(result["middle"]) == n
        assert len(result["lower"]) == n

    def test_leading_nones(self):
        closes = _close(30)
        result = calc_bollinger(closes, 20)
        assert all(v is None for v in result["middle"][:19])
        assert result["middle"][19] is not None

    def test_upper_above_middle_above_lower(self):
        closes = _close(40, step=0.5)
        result = calc_bollinger(closes, 20)
        for u, m, lo in zip(result["upper"], result["middle"], result["lower"]):
            if u is not None:
                assert u >= m >= lo

    def test_middle_equals_ma(self):
        closes = _close(30)
        result_bb = calc_bollinger(closes, 20)
        result_ma = calc_ma(closes, [20])
        for bb_m, ma_m in zip(result_bb["middle"], result_ma["ma_20"]):
            if bb_m is not None and ma_m is not None:
                assert math.isclose(bb_m, ma_m, rel_tol=1e-9)
            else:
                assert bb_m is None and ma_m is None
