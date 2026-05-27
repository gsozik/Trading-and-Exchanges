import ccxt
import pandas as pd
import numpy as np

from data.ohlcv.csv_loader import CsvOHLCVLoader
from data.ohlcv.bybit_loader import BybitOHLCVLoader
from data.ohlcv.moex_loader import MoexOHLCVLoader

from data.orderbook.bybit_orderbook import BybitOrderBookLoader
from data.orderbook.moex_orderbook import MoexOrderBookLoader

from metrics.ohlcv_metrics import make_ohlcv_features
from metrics.orderbook_metrics import orderbook_view, make_orderbook_features

from visualize.orderbook_plots import plot_orderbook_depth


loader = BybitOrderBookLoader()

df = loader.load("SOLUSDT", limit=50)

fig = plot_orderbook_depth(df, depth=50)
fig.show()
