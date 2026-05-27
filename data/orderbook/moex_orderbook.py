import requests
import pandas as pd

from data.base_loader import BaseLoader


class MoexOrderBookLoader(BaseLoader):
    def __init__(
        self,
        engine: str = "stock",
        market: str = "shares",
        board: str = "tqbr"
    ):
        self.engine = engine
        self.market = market
        self.board = board

    def load(self, symbol: str, limit: int = 50) -> pd.DataFrame:
        symbol = symbol.lower()
        board = self.board.lower()

        url = (
            f"https://apim.moex.com/iss/engines/{self.engine}"
            f"/markets/{self.market}/boards/{board}"
            f"/securities/{symbol}/orderbook.json"
        )

        data = requests.get(url).json()
        print(data.keys())
        print(data)
        columns = data["orderbook"]["columns"]
        rows = data["orderbook"]["data"]

        df = pd.DataFrame(rows, columns=columns)

        df = df[["SEQNUM", "SECID", "BUYSELL", "PRICE", "QUANTITY"]]

        df = df.rename(columns={
            "SEQNUM": "timestamp",
            "SECID": "symbol",
            "BUYSELL": "side",
            "PRICE": "price",
            "QUANTITY": "size"
        })

        df["side"] = df["side"].map({"B": "bid", "S": "ask"})
        df["price"] = df["price"].astype(float)
        df["size"] = df["size"].astype(float)

        bids = (
            df[df["side"] == "bid"]
            .sort_values("price", ascending=False)
            .head(limit)
        )

        asks = (
            df[df["side"] == "ask"]
            .sort_values("price", ascending=True)
            .head(limit)
        )

        return pd.concat([bids, asks], ignore_index=True)[
            ["timestamp", "symbol", "side", "price", "size"]
        ]

    def get_top(self, symbol: str, limit: int = 50) -> dict:
        bids, asks = self.get_bids_asks(symbol, limit)

        best_bid = bids.iloc[0]
        best_ask = asks.iloc[0]

        bid_price = best_bid["price"]
        ask_price = best_ask["price"]
        bid_size = best_bid["size"]
        ask_size = best_ask["size"]

        return {
            "symbol": symbol.upper(),
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
        print(f"MOEX ORDER BOOK TOP: {top['symbol']}")
        print("=" * 35)
        print(f"Timestamp : {int(top['timestamp'])}")
        print(f"Best Bid  : {float(top['best_bid']):,.2f}")
        print(f"Best Ask  : {float(top['best_ask']):,.2f}")
        print(f"Bid Size  : {float(top['bid_size']):,.0f}")
        print(f"Ask Size  : {float(top['ask_size']):,.0f}")
        print(f"Mid Price : {float(top['mid_price']):,.2f}")
        print(f"Spread    : {float(top['spread']):.4f}")
        print(f"Imbalance : {float(top['imbalance']):.4f}")
        print("=" * 35)

    def get_bids_asks(self, symbol: str, limit: int = 50):
        df = self.load(symbol, limit)

        bids = df[df["side"] == "bid"].copy()
        asks = df[df["side"] == "ask"].copy()

        return bids, asks



        #TODO: moex order book is a paid service