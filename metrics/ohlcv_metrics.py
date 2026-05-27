import numpy as np
import pandas as pd


def returns(df: pd.DataFrame, column: str = "close") -> pd.Series:
    return df[column].pct_change()


def log_returns(df: pd.DataFrame, column: str = "close") -> pd.Series:
    return np.log(df[column] / df[column].shift(1))


def ma(df: pd.DataFrame, window: int = 20, column: str = "close") -> pd.Series:
    return df[column].rolling(window).mean()


def sma(df: pd.DataFrame, window: int = 20, column: str = "close") -> pd.Series:
    return df[column].rolling(window).mean()


def ema(df: pd.DataFrame, window: int = 20, column: str = "close") -> pd.Series:
    return df[column].ewm(span=window, adjust=False).mean()


def rsi(df: pd.DataFrame, window: int = 14, column: str = "close") -> pd.Series:
    delta = df[column].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    column: str = "close"
) -> pd.DataFrame:
    ema_fast = ema(df, fast, column)
    ema_slow = ema(df, slow, column)

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line

    return pd.DataFrame({
        f"macd_{fast}_{slow}": macd_line,
        f"macd_signal_{signal}": signal_line,
        f"macd_hist_{fast}_{slow}_{signal}": hist
    })


def bollinger_bands(
    df: pd.DataFrame,
    window: int = 20,
    std: float = 2,
    column: str = "close"
) -> pd.DataFrame:
    middle = sma(df, window, column)
    rolling_std = df[column].rolling(window).std()

    upper = middle + std * rolling_std
    lower = middle - std * rolling_std

    return pd.DataFrame({
        f"bb_middle_{window}": middle,
        f"bb_upper_{window}": upper,
        f"bb_lower_{window}": lower,
        f"bb_width_{window}": (upper - lower) / middle,
    })


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

    return tr.ewm(alpha=1 / window, adjust=False).mean()


def stochastic(
    df: pd.DataFrame,
    window: int = 14,
    smooth: int = 3
) -> pd.DataFrame:
    lowest_low = df["low"].rolling(window).min()
    highest_high = df["high"].rolling(window).max()

    k = 100 * (df["close"] - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(smooth).mean()

    return pd.DataFrame({
        f"stoch_k_{window}": k,
        f"stoch_d_{window}_{smooth}": d
    })


def obv(df: pd.DataFrame) -> pd.Series:
    direction = np.sign(df["close"].diff())
    return (direction * df["volume"]).fillna(0).cumsum()


def vwap(df: pd.DataFrame) -> pd.Series:
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    return (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()


def price_range(df: pd.DataFrame) -> pd.Series:
    return (df["high"] - df["low"]) / df["close"]


def body_size(df: pd.DataFrame) -> pd.Series:
    return (df["close"] - df["open"]).abs() / df["open"]


def candle_direction(df: pd.DataFrame) -> pd.Series:
    return np.where(
        df["close"] > df["open"],
        1,
        np.where(df["close"] < df["open"], -1, 0)
    )
# merge all function
def make_ohlcv_features(
    df: pd.DataFrame,
    ma_windows=(10, 20, 50),
    ema_windows=(10, 20, 50),
    rsi_windows=(14,),
    atr_windows=(14,),
    bb_windows=(20,),
    stoch_windows=(14,),
    add_macd: bool = True,
    add_vwap: bool = True,
    add_obv: bool = True,
    dropna: bool = False
) -> pd.DataFrame:
    result = df.copy()

    result["return"] = returns(result)
    result["log_return"] = log_returns(result)

    result["price_range"] = price_range(result)
    result["body_size"] = body_size(result)
    result["candle_direction"] = candle_direction(result)

    for window in ma_windows:
        result[f"ma_{window}"] = ma(result, window)

    for window in ema_windows:
        result[f"ema_{window}"] = ema(result, window)

    for window in rsi_windows:
        result[f"rsi_{window}"] = rsi(result, window)

    for window in atr_windows:
        result[f"atr_{window}"] = atr(result, window)

    for window in bb_windows:
        bb = bollinger_bands(result, window)
        result = pd.concat([result, bb], axis=1)

    for window in stoch_windows:
        stoch = stochastic(result, window)
        result = pd.concat([result, stoch], axis=1)

    if add_macd:
        macd_df = macd(result)
        result = pd.concat([result, macd_df], axis=1)

    if add_vwap:
        result["vwap"] = vwap(result)

    if add_obv:
        result["obv"] = obv(result)

    if dropna:
        result = result.dropna()

    return result