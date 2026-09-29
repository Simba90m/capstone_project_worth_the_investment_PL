import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

st.set_page_config(page_title="Worth the Investment? Explorer", layout="wide")


@st.cache_data
def load_data():
    players = pd.read_parquet(DATA_DIR / "players.parquet")
    value_history = pd.read_parquet(DATA_DIR / "value_history.parquet")
    value_changes = pd.read_parquet(DATA_DIR / "value_changes.parquet")
    return players, value_history, value_changes


players, value_history, value_changes = load_data()
players["has_injury_history"] = players["injury_count"] > 0

st.title("Worth the Investment? Premier League Recruitment Capstone")
st.caption(
    "Companion app for the recruitment capstone: 1,959 Premier League players, three "
    "Transfermarkt/FBref sources modeled with dbt, and three stakeholder hypotheses tested "
    "end to end. Explore the underlying player data behind the findings below."
)

with st.sidebar:
    st.header("Filters")
    positions = sorted(players["position"].dropna().unique())
    picked_positions = st.multiselect("Position", positions, default=positions)
    injury_filter = st.radio(
        "Injury history",
        ["All players", "Any injury on record", "No injury on record"],
        index=0,
    )

filtered = players[players["position"].isin(picked_positions)]
if injury_filter == "Any injury on record":
    filtered = filtered[filtered["has_injury_history"]]
elif injury_filter == "No injury on record":
    filtered = filtered[~filtered["has_injury_history"]]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Players in view", f"{len(filtered):,}")
col2.metric("With injury history", f"{filtered['has_injury_history'].sum():,}")
col3.metric("Total days missed (sum)", f"{int(filtered['total_days_missed'].sum()):,}")
col4.metric("Total matches (sum)", f"{int(filtered['total_matches'].sum()):,}")

st.divider()

st.subheader("The headline finding: does injury history predict value growth?")
st.markdown(
    "Comparing each player's value change between **consecutive valuation snapshots** "
    "(not a simple first-vs-last comparison), split by whether a prior injury was on "
    "record at that point. Breakout-debut snapshots (starting from Transfermarkt's "
    "placeholder floor valuations) are excluded, matching the capstone notebook's method."
)

signal = (
    value_changes.groupby("has_prior_injury")["value_change_pct"]
    .median()
    .mul(100)
    .rename({True: "Any injury on record", False: "No injury on record"})
    .reset_index()
)
signal.columns = ["group", "median_value_change_pct"]
signal["group"] = signal["group"].map({True: "Any injury on record", False: "No injury on record"})

left, right = st.columns([1, 1.4])
with left:
    fig_signal = px.bar(
        signal,
        x="group",
        y="median_value_change_pct",
        color="group",
        text=signal["median_value_change_pct"].map(lambda v: f"{v:.2f}%"),
        labels={"median_value_change_pct": "Median value change (%)", "group": ""},
        color_discrete_map={"Any injury on record": "#D6006C", "No injury on record": "#0F9B8E"},
    )
    fig_signal.update_traces(textposition="outside")
    fig_signal.update_layout(showlegend=False)
    st.plotly_chart(fig_signal, width="stretch")
with right:
    st.markdown(
        "Any injury history on record predicts **0% median value growth** at the next "
        "valuation snapshot, versus **+4.35%** for players with no injury on record "
        "(n = 18,846 vs 10,478 snapshots). This held up better than the recruitment "
        "team's original value-forecasting model, which only hit 22.7% directional "
        "accuracy on held-out players, worse than a coin flip."
    )
    st.caption("Position was not a statistically significant predictor of injury risk (p = 0.61).")

st.divider()

left2, right2 = st.columns([1.3, 1])

with left2:
    st.subheader("Value change by injury recency")
    bucket_order = ["recent (<=90 days)", "moderate (91-365 days)", "distant (>365 days)", "no prior injury"]
    fig_box = px.box(
        value_changes,
        x="recency_bucket",
        y=value_changes["value_change_pct"] * 100,
        category_orders={"recency_bucket": bucket_order},
        labels={"y": "Value change at next valuation (%)", "recency_bucket": ""},
        points=False,
    )
    fig_box.update_yaxes(range=[-60, 60])
    st.plotly_chart(fig_box, width="stretch")
    st.caption("Y-axis clipped to +/-60% so the boxes stay readable; a handful of breakout-debut outliers run far higher.")

with right2:
    st.subheader("Players by position")
    pos_stats = filtered.groupby("position").agg(
        players=("player_id", "count"),
        injured=("has_injury_history", "sum"),
    ).reset_index()
    pos_stats["injury_rate_pct"] = (pos_stats["injured"] / pos_stats["players"] * 100).round(1)
    fig_pos = px.bar(
        pos_stats.sort_values("injury_rate_pct"),
        x="injury_rate_pct",
        y="position",
        orientation="h",
        labels={"injury_rate_pct": "Injury rate (%)", "position": ""},
        color_discrete_sequence=["#0F9B8E"],
    )
    st.plotly_chart(fig_pos, width="stretch")

st.divider()
st.subheader("Look up a player's value history")
name_options = sorted(filtered["canonical_name"].dropna().unique())
if name_options:
    picked_name = st.selectbox("Player", name_options)
    row = filtered[filtered["canonical_name"] == picked_name].iloc[0]
    hist = value_history[value_history["player_id"] == row["player_id"]].sort_values("valuation_date")

    st.markdown(
        f"**{picked_name}**, {row['position']}"
        + (f" ({row['sub_position']})" if pd.notna(row["sub_position"]) else "")
        + f". Injuries on record: {int(row['injury_count'])}, "
        f"total days missed: {int(row['total_days_missed'])}, "
        f"total matches (FBref): {int(row['total_matches'])}."
    )
    if len(hist) >= 2:
        fig_hist = px.line(
            hist, x="valuation_date", y="market_value_in_eur", markers=True,
            labels={"valuation_date": "", "market_value_in_eur": "Market value (EUR)"},
        )
        st.plotly_chart(fig_hist, width="stretch")
    else:
        st.info("Not enough valuation snapshots for this player to plot a trend.")
else:
    st.info("No players match the current filters.")

st.divider()
st.caption(
    "Data: Transfermarkt player values and injury history, plus FBref performance stats, "
    "for 1,959 Premier League players. Modeled with dbt (staging to marts, tested) on DuckDB. "
    "Full write-up, dbt models, and notebooks: "
    "[GitHub repo](https://github.com/Simba90m/capstone_project_worth_the_investment_PL)."
)
