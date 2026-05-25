import ccxt
import pandas as pd
import numpy as np

from data.ohlcv.csv_loader import CsvOHLCVLoader
from data.ohlcv.bybit_loader import BybitOHLCVLoader
from data.ohlcv.moex_loader import MoexOHLCVLoader

loader = MoexOHLCVLoader(
    ticker="SBER",
    timeframe="1h",
    start="2024-01-01",
    end="2024-12-31"
)

df = loader.load()
print(df.head())