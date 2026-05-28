import sys
import time
from pathlib import Path

import pandas as pd
from pybit.unified_trading import WebSocket

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from metrics.orderbook_metrics import orderbook_view, make_orderbook_features


def storage_path(symbol: str, filename: str) -> Path:
    path = ROOT_DIR / "storage" / symbol
    path.mkdir(parents=True, exist_ok=True)
    return path / filename


def append_csv(rows: list[dict], path: Path):
    if not rows:
        return

    pd.DataFrame(rows).to_csv(
        path,
        mode="a",
        index=False,
        header=not path.exists()
    )


def update_book(book: dict, message: dict):
    data = message["data"]

    if message["type"] == "snapshot":
        book["bid"].clear()
        book["ask"].clear()

    for price, size in data.get("b", []):
        price = float(price)
        size = float(size)

        if size == 0:
            book["bid"].pop(price, None)
        else:
            book["bid"][price] = size

    for price, size in data.get("a", []):
        price = float(price)
        size = float(size)

        if size == 0:
            book["ask"].pop(price, None)
        else:
            book["ask"][price] = size


def book_to_df(book: dict, symbol: str, timestamp: int, depth: int) -> pd.DataFrame:
    rows = []

    bids = sorted(book["bid"].items(), key=lambda x: x[0], reverse=True)[:depth]
    asks = sorted(book["ask"].items(), key=lambda x: x[0])[:depth]

    for level, (price, size) in enumerate(bids, start=1):
        rows.append({
            "timestamp": timestamp,
            "symbol": symbol,
            "side": "bid",
            "level": level,
            "price": price,
            "size": size,
        })

    for level, (price, size) in enumerate(asks, start=1):
        rows.append({
            "timestamp": timestamp,
            "symbol": symbol,
            "side": "ask",
            "level": level,
            "price": price,
            "size": size,
        })

    return pd.DataFrame(rows)


def print_live_snapshot(df: pd.DataFrame, symbol: str):
    view = orderbook_view(df).head(5)
    features = make_orderbook_features(df).iloc[0]

    print("\n" + "=" * 90)
    print(f"Symbol      : {symbol}")
    print(f"Timestamp   : {df['timestamp'].iloc[0]}")

    print("\nTOP ORDERBOOK:")
    print(view)

    print("\nFEATURES:")
    print(f"Best Bid    : {features['best_bid']}")
    print(f"Best Ask    : {features['best_ask']}")
    print(f"Mid Price   : {features['mid_price']}")
    print(f"Spread      : {features['spread']}")
    print(f"Microprice  : {features['microprice']}")
    print(f"Imbalance 1 : {features['imbalance_1']}")
    print(f"Imbalance 5 : {features['imbalance_5']}")
    print(f"Imbalance 10: {features['imbalance_10']}")


def parse_trades(message: dict, seen_trades: set) -> list[dict]:
    rows = []
    local_timestamp = int(time.time() * 1000)

    for trade in message.get("data", []):
        trade_id = trade.get("i")

        if trade_id in seen_trades:
            continue

        seen_trades.add(trade_id)

        rows.append({
            "local_timestamp": local_timestamp,
            "trade_timestamp": trade.get("T"),
            "symbol": trade.get("s"),
            "side": trade.get("S"),
            "price": float(trade.get("p")),
            "size": float(trade.get("v")),
            "trade_id": trade_id,
            "tick_direction": trade.get("L"),
            "is_block_trade": trade.get("BT"),
            "seq": trade.get("seq"),
        })

    return rows


def live_orderbook(
    symbol: str,
    depth: int = 50,
    category: str = "linear",
    log_orderbook: bool = True,
    log_trades: bool = True,
    print_book: bool = True,
):
    """
    WebSocket-сборщик стакана и сделок Bybit.

    log_orderbook=True:
        сохраняет восстановленный стакан в:
        storage/{symbol}/{symbol}_orderbook_ws.csv

    log_trades=True:
        сохраняет реальные сделки в:
        storage/{symbol}/{symbol}_trades_ws.csv

    print_book=True:
        печатает текущую верхушку стакана и метрики.
    """

    book = {"bid": {}, "ask": {}}
    seen_trades = set()

    orderbook_file = storage_path(symbol, f"{symbol}_orderbook_ws.csv")
    trades_file = storage_path(symbol, f"{symbol}_trades_ws.csv")

    ws = WebSocket(
        testnet=False,
        channel_type=category,
    )

    def handle_orderbook(message):
        update_book(book, message)

        timestamp = message.get("ts")
        local_timestamp = int(time.time() * 1000)

        df = book_to_df(
            book=book,
            symbol=symbol,
            timestamp=timestamp,
            depth=depth,
        )

        if df.empty:
            return

        df["local_timestamp"] = local_timestamp
        df["message_type"] = message.get("type")
        df["seq"] = message.get("data", {}).get("seq")
        df["matching_engine_timestamp"] = message.get("data", {}).get("cts")

        if log_orderbook:
            append_csv(df.to_dict("records"), orderbook_file)

        if print_book:
            print_live_snapshot(
                df[["timestamp", "symbol", "side", "level", "price", "size"]],
                symbol
            )

    def handle_trades(message):
        rows = parse_trades(message, seen_trades)

        if log_trades:
            append_csv(rows, trades_file)

        if rows:
            last = rows[-1]
            print(
                f"[TRADE] {symbol} | "
                f"{last['side']} | "
                f"price={last['price']} | "
                f"size={last['size']}"
            )

    ws.orderbook_stream(
        depth=depth,
        symbol=symbol,
        callback=handle_orderbook,
    )

    if log_trades:
        ws.trade_stream(
            symbol=symbol,
            callback=handle_trades,
        )

    print(f"WebSocket started: {symbol}")
    print(f"Orderbook logging: {log_orderbook} -> {orderbook_file}")
    print(f"Trades logging   : {log_trades} -> {trades_file}")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopped")


