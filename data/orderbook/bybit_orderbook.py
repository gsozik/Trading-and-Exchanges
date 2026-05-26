import pandas as pd
from pybit.unified_trading import HTTP

from data.base_loader import BaseLoader


class BybitOrderBookLoader(BaseLoader):
    def __init__(self, category: str = "linear", testnet: bool = False):
        self.category = category
        self.session = HTTP(testnet=testnet)

    def load(self, symbol: str, limit: int = 50) -> pd.DataFrame:
        data = self.session.get_orderbook(
            category=self.category,
            symbol=symbol,
            limit=limit
        )

        result = data["result"]

        bids = pd.DataFrame(result["b"], columns=["price", "size"])
        asks = pd.DataFrame(result["a"], columns=["price", "size"])

        bids["side"] = "bid"
        asks["side"] = "ask"

        df = pd.concat([bids, asks], ignore_index=True)

        df["price"] = df["price"].astype(float)
        df["size"] = df["size"].astype(float)
        df["symbol"] = result["s"]
        df["timestamp"] = result["ts"]

        return df[["timestamp", "symbol", "side", "price", "size"]]

    def get_top(self, symbol: str, limit: int = 50) -> dict:
        df = self.load(symbol, limit)

        best_bid = df[df["side"] == "bid"].iloc[0]
        best_ask = df[df["side"] == "ask"].iloc[0]

        bid_price = best_bid["price"]
        ask_price = best_ask["price"]
        bid_size = best_bid["size"]
        ask_size = best_ask["size"]

        return {
            "symbol": symbol,
            "timestamp": best_bid["timestamp"],
            "best_bid": bid_price,
            "best_ask": ask_price,
            "bid_size": bid_size,
            "ask_size": ask_size,
            "mid_price": (bid_price + ask_price) / 2,
            "spread": ask_price - bid_price,
            "imbalance": bid_size / (bid_size + ask_size),
        }

    def print_top(self, symbol: str, limit: int = 50):
        top = self.get_top(symbol, limit)

        print("=" * 35)
        print(f"ORDER BOOK TOP: {top['symbol']}")
        print("=" * 35)
        print(f"Timestamp : {int(top['timestamp'])}")
        print(f"Best Bid  : {float(top['best_bid']):,.2f}")
        print(f"Best Ask  : {float(top['best_ask']):,.2f}")
        print(f"Bid Size  : {float(top['bid_size']):,.6f}")
        print(f"Ask Size  : {float(top['ask_size']):,.6f}")
        print(f"Mid Price : {float(top['mid_price']):,.2f}")
        print(f"Spread    : {float(top['spread']):.4f}")
        print(f"Imbalance : {float(top['imbalance']):.4f}")
        print("=" * 35)

    def get_bids_asks(self, symbol: str, limit: int = 50):
        df = self.load(symbol, limit)

        bids = df[df["side"] == "bid"].copy()
        asks = df[df["side"] == "ask"].copy()

        return bids, asks