import pandas as pd


def bids(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["side"] == "bid"].sort_values("price", ascending=False).reset_index(drop=True)


def asks(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["side"] == "ask"].sort_values("price", ascending=True).reset_index(drop=True)


def best_bid(df: pd.DataFrame) -> float:
    return bids(df).iloc[0]["price"]


def best_ask(df: pd.DataFrame) -> float:
    return asks(df).iloc[0]["price"]


def bid_size(df: pd.DataFrame) -> float:
    return bids(df).iloc[0]["size"]


def ask_size(df: pd.DataFrame) -> float:
    return asks(df).iloc[0]["size"]


def mid_price(df: pd.DataFrame) -> float:
    return (best_bid(df) + best_ask(df)) / 2


def spread(df: pd.DataFrame) -> float:
    return best_ask(df) - best_bid(df)


def relative_spread(df: pd.DataFrame) -> float:
    return spread(df) / mid_price(df)


def microprice(df: pd.DataFrame) -> float:
    bid = best_bid(df)
    ask = best_ask(df)
    bid_vol = bid_size(df)
    ask_vol = ask_size(df)

    return (bid * ask_vol + ask * bid_vol) / (bid_vol + ask_vol)


def microprice_diff(df: pd.DataFrame) -> float:
    return microprice(df) - mid_price(df)


def microprice_diff_pct(df: pd.DataFrame) -> float:
    return microprice_diff(df) / mid_price(df)


def imbalance(df: pd.DataFrame, depth: int = 1) -> float:
    bid_vol = bids(df).head(depth)["size"].sum()
    ask_vol = asks(df).head(depth)["size"].sum()

    return (bid_vol - ask_vol) / (bid_vol + ask_vol)


def volume(df: pd.DataFrame, depth: int = 10) -> dict:
    bid_vol = bids(df).head(depth)["size"].sum()
    ask_vol = asks(df).head(depth)["size"].sum()

    return {
        f"bid_volume_{depth}": bid_vol,
        f"ask_volume_{depth}": ask_vol,
        f"total_volume_{depth}": bid_vol + ask_vol,
    }


def notional(df: pd.DataFrame, depth: int = 10) -> dict:
    bid_df = bids(df).head(depth)
    ask_df = asks(df).head(depth)

    bid_notional = (bid_df["price"] * bid_df["size"]).sum()
    ask_notional = (ask_df["price"] * ask_df["size"]).sum()

    return {
        f"bid_notional_{depth}": bid_notional,
        f"ask_notional_{depth}": ask_notional,
        f"total_notional_{depth}": bid_notional + ask_notional,
    }


def liquidity_imbalance(df: pd.DataFrame, depth: int = 10) -> float:
    bid_df = bids(df).head(depth)
    ask_df = asks(df).head(depth)

    bid_notional = (bid_df["price"] * bid_df["size"]).sum()
    ask_notional = (ask_df["price"] * ask_df["size"]).sum()

    return (bid_notional - ask_notional) / (bid_notional + ask_notional)


def buy_slippage(df: pd.DataFrame, quantity: float) -> float | None:
    ask_df = asks(df)

    remaining = quantity
    cost = 0

    for _, row in ask_df.iterrows():
        trade_size = min(remaining, row["size"])
        cost += trade_size * row["price"]
        remaining -= trade_size

        if remaining <= 0:
            break

    if remaining > 0:
        return None

    avg_price = cost / quantity

    return avg_price - best_ask(df)


def sell_slippage(df: pd.DataFrame, quantity: float) -> float | None:
    bid_df = bids(df)

    remaining = quantity
    revenue = 0

    for _, row in bid_df.iterrows():
        trade_size = min(remaining, row["size"])
        revenue += trade_size * row["price"]
        remaining -= trade_size

        if remaining <= 0:
            break

    if remaining > 0:
        return None

    avg_price = revenue / quantity

    return best_bid(df) - avg_price


def buy_slippage_pct(df: pd.DataFrame, quantity: float) -> float | None:
    slip = buy_slippage(df, quantity)

    if slip is None:
        return None

    return slip / best_ask(df)


def sell_slippage_pct(df: pd.DataFrame, quantity: float) -> float | None:
    slip = sell_slippage(df, quantity)

    if slip is None:
        return None

    return slip / best_bid(df)


def orderbook_view(df: pd.DataFrame) -> pd.DataFrame:
    bid_df = bids(df)
    ask_df = asks(df)

    levels = min(len(bid_df), len(ask_df))

    return pd.DataFrame({
        "level": range(1, levels + 1),
        "bid_price": bid_df["price"].head(levels).values,
        "bid_size": bid_df["size"].head(levels).values,
        "ask_price": ask_df["price"].head(levels).values,
        "ask_size": ask_df["size"].head(levels).values,
    })


def make_orderbook_features(
    df: pd.DataFrame,
    imbalance_depths=(1, 5, 10),
    volume_depths=(5, 10, 20),
    notional_depths=(5, 10, 20),
    slippage_quantities=(0.1, 0.5, 1),
) -> pd.DataFrame:
    row = {
        "timestamp": df["timestamp"].iloc[0],
        "symbol": df["symbol"].iloc[0],

        "best_bid": best_bid(df),
        "best_ask": best_ask(df),
        "bid_size": bid_size(df),
        "ask_size": ask_size(df),

        "mid_price": mid_price(df),
        "spread": spread(df),
        "relative_spread": relative_spread(df),

        "microprice": microprice(df),
        "microprice_diff": microprice_diff(df),
        "microprice_diff_pct": microprice_diff_pct(df),
    }

    for depth in imbalance_depths:
        row[f"imbalance_{depth}"] = imbalance(df, depth)

    for depth in volume_depths:
        row.update(volume(df, depth))

    for depth in notional_depths:
        row.update(notional(df, depth))
        row[f"liquidity_imbalance_{depth}"] = liquidity_imbalance(df, depth)

    for quantity in slippage_quantities:
        row[f"buy_slippage_{quantity}"] = buy_slippage(df, quantity)
        row[f"sell_slippage_{quantity}"] = sell_slippage(df, quantity)
        row[f"buy_slippage_pct_{quantity}"] = buy_slippage_pct(df, quantity)
        row[f"sell_slippage_pct_{quantity}"] = sell_slippage_pct(df, quantity)

    return pd.DataFrame([row])