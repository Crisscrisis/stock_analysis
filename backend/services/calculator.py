"""Pure technical indicator calculations — no I/O, no side effects."""
from __future__ import annotations


def calc_ma(closes: list[float], periods: list[int]) -> dict[str, list[float | None]]:
    """Calculate simple moving averages for each period.

    Returns dict like {"ma_5": [...], "ma_10": [...]} where leading values
    without enough data are None.
    """
    result: dict[str, list[float | None]] = {}
    n = len(closes)
    for period in periods:
        key = f"ma_{period}"
        if n == 0:
            result[key] = []
            continue
        values: list[float | None] = [None] * n
        for i in range(period - 1, n):
            window = closes[i - period + 1 : i + 1]
            values[i] = sum(window) / period
        result[key] = values
    return result


def _ema(values: list[float], period: int) -> list[float | None]:
    """Exponential moving average; leading Nones until period-1 data points seen."""
    n = len(values)
    result: list[float | None] = [None] * n
    if n < period:
        return result
    k = 2.0 / (period + 1)
    # Seed with SMA of first `period` values
    result[period - 1] = sum(values[:period]) / period
    for i in range(period, n):
        prev = result[i - 1]
        result[i] = values[i] * k + prev * (1 - k)  # type: ignore[operator]
    return result


def calc_macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, list[float | None]]:
    """MACD line, signal line, and histogram."""
    n = len(closes)
    fast_ema = _ema(closes, fast)
    slow_ema = _ema(closes, slow)

    macd_line: list[float | None] = [None] * n
    for i in range(n):
        f, s = fast_ema[i], slow_ema[i]
        if f is not None and s is not None:
            macd_line[i] = f - s

    # Signal = EMA of MACD line (only over non-None values)
    # We compute it in-place over the full array
    signal_line: list[float | None] = [None] * n
    macd_not_none = [(i, v) for i, v in enumerate(macd_line) if v is not None]
    if len(macd_not_none) >= signal:
        k = 2.0 / (signal + 1)
        start_idx = macd_not_none[signal - 1][0]
        seed = sum(v for _, v in macd_not_none[:signal]) / signal
        signal_line[start_idx] = seed
        # Walk through remaining macd values
        prev = seed
        for i in range(start_idx + 1, n):
            if macd_line[i] is not None:
                prev = macd_line[i] * k + prev * (1 - k)  # type: ignore[operator]
                signal_line[i] = prev

    histogram: list[float | None] = [None] * n
    for i in range(n):
        m, s = macd_line[i], signal_line[i]
        if m is not None and s is not None:
            histogram[i] = m - s

    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def calc_rsi(closes: list[float], period: int = 14) -> list[float | None]:
    """Wilder's RSI. Returns list of same length as closes; leading values None."""
    n = len(closes)
    result: list[float | None] = [None] * n
    if n <= period:
        return result

    gains = []
    losses = []
    for i in range(1, n):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))

    # Initial averages (SMA seed)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    def _rsi(ag: float, al: float) -> float | None:
        if ag == 0 and al == 0:
            return None
        if al == 0:
            return 100.0
        rs = ag / al
        return 100.0 - (100.0 / (1.0 + rs))

    result[period] = _rsi(avg_gain, avg_loss)

    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        result[i] = _rsi(avg_gain, avg_loss)

    return result


def calc_bollinger(
    closes: list[float],
    period: int = 20,
    num_std: float = 2.0,
) -> dict[str, list[float | None]]:
    """Bollinger Bands: upper, middle (SMA), lower."""
    import math

    n = len(closes)
    upper: list[float | None] = [None] * n
    middle: list[float | None] = [None] * n
    lower: list[float | None] = [None] * n

    for i in range(period - 1, n):
        window = closes[i - period + 1 : i + 1]
        sma = sum(window) / period
        variance = sum((x - sma) ** 2 for x in window) / period
        std = math.sqrt(variance)
        middle[i] = sma
        upper[i] = sma + num_std * std
        lower[i] = sma - num_std * std

    return {"upper": upper, "middle": middle, "lower": lower}
