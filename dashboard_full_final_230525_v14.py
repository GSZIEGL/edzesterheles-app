
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Edzésterhelés – Teljes Elemző Rendszer v14")

# ========== HELPER FÜGGVÉNYEK ==========

@st.cache_data
def load_data(uploaded_files):
    dfs = []
    for file in uploaded_files:
        excel = pd.ExcelFile(file)
        for sheet_name in excel.sheet_names:
            df = excel.parse(sheet_name)
            df["Forrás"] = sheet_name
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

def normalize_series(series):
    min_val = series.min()
    max_val = series.max()
    if max_val - min_val == 0:
        return series * 0
    return (series - min_val) / (max_val - min_val)

def plot_pizza(df, selected_players, selected_features, benchmark_dict, team_avg_df, chart_type="combined"):
    fig = go.Figure()
    angles = list(range(len(selected_features)))
    labels = selected_features

    if chart_type == "combined":
        for player in selected_players:
            player_values = df[df["Név"] == player][selected_features].mean()
            fig.add_trace(go.Scatterpolar(
                r=normalize_series(player_values),
                theta=labels,
                fill='toself',
                name=player
            ))
    else:
        for player in selected_players:
            player_values = df[df["Név"] == player][selected_features].mean()
            fig.add_trace(go.Scatterpolar(
                r=normalize_series(player_values),
                theta=labels,
                fill='toself',
                name=player
            ))

    # Team average
    team_avg = team_avg_df[selected_features].mean()
    fig.add_trace(go.Scatterpolar(
        r=normalize_series(team_avg),
        theta=labels,
        fill='toself',
        name="Csapatátlag",
        line=dict(color="black", dash="dash")
    ))

    # Benchmark
    benchmark_values = pd.Series([benchmark_dict.get(col, 0) for col in selected_features], index=selected_features)
    fig.add_trace(go.Scatterpolar(
        r=normalize_series(benchmark_values),
        theta=labels,
        name="Benchmark",
        line=dict(color="green", dash="dot")
    ))

    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=True)
    return fig

def plot_trend(df, selected_players, feature, benchmark_value):
    fig = go.Figure()
    for player in selected_players:
        player_data = df[df["Név"] == player]
        fig.add_trace(go.Scatter(x=player_data["Forrás"], y=player_data[feature], mode="lines+markers", name=player))

    # Benchmark vonal
    fig.add_trace(go.Scatter(
        x=df["Forrás"].unique(), y=[benchmark_value] * len(df["Forrás"].unique()),
        mode="lines", name="Benchmark", line=dict(color="green", dash="dash")
    ))

    fig.update_layout(title=f"Trend – {feature}", xaxis_title="Hét", yaxis_title=feature)
    return fig

# ========== ADATBETÖLTÉS ==========

uploaded_files = st.file_uploader("Excel fájl(ok) feltöltése", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    df_raw = load_data(uploaded_files)
    df_raw = df_raw.dropna(subset=["Név"])
    all_players = df_raw["Név"].unique().tolist()
    all_features = df_raw.select_dtypes(include='number').columns.tolist()
    weeks = df_raw["Forrás"].unique().tolist()

    # ========== SZŰRŐK OLDALSÁVBAN ==========

    with st.sidebar:
        st.header("Szűrők")
        selected_players = st.multiselect("Játékosok", all_players, default=all_players)
        selected_features = st.multiselect("Mutatók", all_features, default=all_features)
        selected_weeks = st.multiselect("Hetek", weeks, default=weeks)

    df_filtered = df_raw[df_raw["Név"].isin(selected_players) & df_raw["Forrás"].isin(selected_weeks)]
    team_avg_df = df_raw[df_raw["Forrás"].isin(selected_weeks)]

    # ========== BENCHMARK DICTIONARY ==========

    benchmark_dict = {
        "Teljes táv (m)": 15000,
        "Táv/perc": 100,
        "Táv zóna 4 (m)": 1200,
        "Táv zóna 5 (m)": 300,
        "Sprintek száma": 25,
        "Gyorsulások száma": 50,
        "Izomterhelés": 80,
        "Edzésterhelés": 300,
        "Max sebesség": 32
    }

    st.header("Pizzadiagram")
    pizza_view = st.radio("Pizza nézet", ["Egy pizza", "Játékosonként külön"], horizontal=True)
    pizza_chart_type = "combined" if pizza_view == "Egy pizza" else "per_player"
    st.plotly_chart(plot_pizza(df_filtered, selected_players, selected_features, benchmark_dict, team_avg_df, pizza_chart_type), use_container_width=True)

    # ========== TREND DIAGRAM ==========

    st.header("Trenddiagramok (mutatónként)")
    for feature in selected_features:
        benchmark_value = benchmark_dict.get(feature, 0)
        st.plotly_chart(plot_trend(df_filtered, selected_players, feature, benchmark_value), use_container_width=True)

    # ========== BENCHMARK TÁBLÁZAT ==========

    st.header("Benchmark táblázat")
    bench_df = pd.DataFrame({
        "Mutató": list(benchmark_dict.keys()),
        "Benchmark érték": list(benchmark_dict.values())
    })
    st.dataframe(bench_df, use_container_width=True)

else:
    st.info("Kérlek, tölts fel legalább egy Excel fájlt.")
