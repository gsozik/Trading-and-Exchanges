import pandas as pd
import plotly.graph_objects as go


def plot_orderbook_depth(
    df: pd.DataFrame,
    depth: int = 50,
    title: str | None = None,
    show_mid: bool = True,
    show_best: bool = True,
):
    bids = (
        df[df["side"] == "bid"]
        .sort_values("price", ascending=False)
        .head(depth)
        .copy()
    )

    asks = (
        df[df["side"] == "ask"]
        .sort_values("price", ascending=True)
        .head(depth)
        .copy()
    )

    bids["cum_size"] = bids["size"].cumsum()
    asks["cum_size"] = asks["size"].cumsum()

    bids = bids.sort_values("price", ascending=True)

    symbol = df["symbol"].iloc[0]
    timestamp = df["timestamp"].iloc[0]

    best_bid = bids["price"].max()
    best_ask = asks["price"].min()
    mid = (best_bid + best_ask) / 2
    spread = best_ask - best_bid

    if title is None:
        title = f"{symbol} Order Book Depth"

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=bids["price"],
            y=bids["cum_size"],
            mode="lines",
            name="Bids",
            line=dict(color="#00C176", width=3),
            fill="tozeroy",
            fillcolor="rgba(0, 193, 118, 0.45)",
            hovertemplate=(
                "<b>BID</b><br>"
                "Price: %{x}<br>"
                "Cumulative size: %{y}<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=asks["price"],
            y=asks["cum_size"],
            mode="lines",
            name="Asks",
            line=dict(color="#FF3B69", width=3),
            fill="tozeroy",
            fillcolor="rgba(255, 59, 105, 0.45)",
            hovertemplate=(
                "<b>ASK</b><br>"
                "Price: %{x}<br>"
                "Cumulative size: %{y}<extra></extra>"
            ),
        )
    )

    if show_mid:
        fig.add_vline(
            x=mid,
            line_width=2,
            line_dash="dash",
            line_color="white",
        )



    if show_best:
        fig.add_vline(
            x=best_bid,
            line_width=1,
            line_dash="dot",
            line_color="#00C176",
        )

        fig.add_vline(
            x=best_ask,
            line_width=1,
            line_dash="dot",
            line_color="#FF3B69",
        )

    fig.update_layout(
        template="plotly_dark",
        title=dict(
            text=(
                f"{title}<br>"
                f"<sup>timestamp: {timestamp} | "
                f"best bid: {best_bid:.6f} | "
                f"best ask: {best_ask:.6f} | "
                f"spread: {spread:.6f}</sup>"
            ),
            x=0.5,
            xanchor="center",
        ),
        xaxis=dict(
            title="Price",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Cumulative Size",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
        ),
        plot_bgcolor="#05070D",
        paper_bgcolor="#05070D",
        hovermode="x unified",
        height=650,
        margin=dict(l=60, r=40, t=90, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    return fig