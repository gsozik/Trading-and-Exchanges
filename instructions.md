
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