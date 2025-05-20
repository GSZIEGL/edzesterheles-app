
# Streamlit edzésterhelés dashboard – végleges, fejlesztett verzió pizzadiagramokkal és strukturált szűrőpanellel

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Edzésterhelés Dashboard", layout="wide")

st.title("⚽ Edzésterhelés – Interaktív Elemző Rendszer")

uploaded_file = st.file_uploader("📤 Tölts fel egy Excel fájlt (hetek = munkalapok)", type="xlsx")

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    dfs = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["Hét"] = sheet
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

def normalize_series(s):
    return (s - s.min()) / (s.max() - s.min()) * 100 if s.max() != s.min() else s

def pizza_chart(df, mutatok, ref_dict, title):
    df = df[mutatok].mean().dropna()
    pizza_df = pd.DataFrame({
        "Mutató": df.index,
        "Érték": df.values,
        "Benchmark": [ref_dict.get(m, None) for m in df.index]
    })
    fig = px.bar_polar(pizza_df, r="Érték", theta="Mutató", color="Mutató",
                       title=title, template="plotly_dark", range_r=[0, max(pizza_df["Benchmark"].max(), pizza_df["Érték"].max()) * 1.2])
    return fig

if uploaded_file:
    df = load_data(uploaded_file)
    df = df[df["Játékos neve"].notna()]

    st.sidebar.header("🎛 Szűrési panel")

    with st.sidebar.expander("🧍‍♂️ Játékos"):
        players = sorted(df["Játékos neve"].dropna().unique())
        player = st.selectbox("Válassz játékost", players)

    with st.sidebar.expander("🏷 Típus és Hét"):
        tipusok = df["Típus"].dropna().unique().tolist()
        tipus = st.selectbox("Típus", ["Összes"] + tipusok)
        hetek = df["Hét"].dropna().unique().tolist()
        selected_weeks = st.multiselect("Hetek", hetek, default=hetek)

    with st.sidebar.expander("📊 Mutatók kiválasztása"):
        mutatok = [c for c in df.columns if df[c].dtype in ["int64", "float64"] and c not in ["Kor", "Évfolyam"]]
        selected_metrics = st.multiselect("Mutatók", mutatok, default=[])

    df_player = df[(df["Játékos neve"] == player) & (df["Hét"].isin(selected_weeks))]
    if tipus != "Összes":
        df_player = df_player[df_player["Típus"] == tipus]

    df_team = df[df["Hét"].isin(selected_weeks)]
    if tipus != "Összes":
        df_team = df_team[df_team["Típus"] == tipus]

    ref_values = {
        "Teljes táv [m]": 5500,
        "Táv/perc [m/perc]": 100,
        "Max sebesség [km/h]": 30,
        "Sprintek száma": 25,
        "Izomterhelés": 65,
        "HRV (RMSSD)": 60,
        "Átlagos pulzus [bpm]": 160,
        "Zóna 5-6 táv": 500,
        "Zóna 5 gyorsulás": 10,
        "Zóna 5 lassulás": 10
    }

    st.subheader(f"📌 {player} teljesítménye vs csapat vs benchmark")
    if selected_metrics:
        avg_player = df_player[selected_metrics].mean()
        avg_team = df_team[selected_metrics].mean()
        comp_df = pd.DataFrame({
            "Mutató": selected_metrics,
            "Játékos": [avg_player.get(m, None) for m in selected_metrics],
            "Csapat": [avg_team.get(m, None) for m in selected_metrics],
            "Benchmark": [ref_values.get(m, None) for m in selected_metrics]
        })
        fig_comp = px.bar(comp_df, x="Mutató", y=["Játékos", "Csapat", "Benchmark"], barmode="group")
        st.plotly_chart(fig_comp, use_container_width=True)

        st.subheader("🍕 Pizzadiagram – Átlagos értékek")
        fig_pizza = pizza_chart(df_player, selected_metrics, ref_values, "Pizza diagram – Játékos vs Benchmark")
        st.plotly_chart(fig_pizza, use_container_width=True)

        st.subheader("📈 Normalizált trenddiagram")
        trend_df = df_player.groupby("Hét")[selected_metrics].mean().reset_index()
        for col in selected_metrics:
            if col in trend_df.columns:
                trend_df[col] = normalize_series(trend_df[col])
        fig_trend = px.line(trend_df, x="Hét", y=selected_metrics, markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)

    st.subheader("📋 Adattábla")
    st.dataframe(df_player[selected_metrics + ["Hét", "Típus"]] if selected_metrics else df_player)
else:
    st.info("Tölts fel egy Data.xlsx fájlt a kezdéshez.")
