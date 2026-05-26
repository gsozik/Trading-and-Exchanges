import ccxt
import pandas as pd
import numpy as np

from data.ohlcv.csv_loader import CsvOHLCVLoader
from data.ohlcv.bybit_loader import BybitOHLCVLoader
from data.ohlcv.moex_loader import MoexOHLCVLoader

from data.orderbook.bybit_orderbook import BybitOrderBookLoader


loader = BybitOrderBookLoader(category="linear")

df = loader.print_top("BTCUSDT", limit=50)
print(df)