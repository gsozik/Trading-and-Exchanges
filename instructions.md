
# Use BybitOHLCVLoader

loader = BybitOHLCVLoader(
    symbol="BTC/USDT",
    timeframe="1h",
    start="2024-01-01",
    end="2024-12-31"
)

df = loader.load()
print(df.head())

# Use CsvOHLCVLoader

loader = CsvOHLCVLoader(
    path="storage/BTC_USDT/2024-01-01-2024-12-31.csv",
    start="2024-01-01",
    end="2024-12-31"
)

df = loader.load()
print(df.head())

# Use MoexOHLCVLoader

loader = MoexOHLCVLoader(
    ticker="SBER",
    timeframe="1h",
    start="2024-01-01",
    end="2024-12-31"
)

df = loader.load()
print(df.head())

# Use BybitOrderBookLoader

loader = BybitOrderBookLoader(category="linear")

df = loader.load("BTCUSDT", limit=50)
print(df)

agg = loader.get_top("BTCUSDT", limit=50)
print(agg)

loader.print_top("BTCUSDT", limit=50) 

only_bd = loader.get_bids_asks("BTCUSDT", limit=50)
print(only_bd)