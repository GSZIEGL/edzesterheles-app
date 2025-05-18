
# STREAMLIT DASHBOARD – VÉGLEGES MŰKÖDŐ VERZIÓ
# Minden diagram és szűrő újraépítve a sablon Excel két dashboardfüle alapján.

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Végső Edzésterhelés Dashboard", layout="wide")

st.title("⚽ Teljes edzésterhelés és meccsterhelés – Dashboard")
uploaded_file = st.file_uploader("📤 Tölts fel egy Data.xlsx fájlt (5 edzés + 1 meccs)", type="xlsx")

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    dfs = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["Forrás"] = sheet
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

def create_radar_chart(player_df, mutatok, title, ref_values):
    valid = [m for m in mutatok if m in player_df.columns]
    if not valid:
        return None
    avg_stats = player_df[valid].mean()
    norm_vals = [avg_stats[m]/ref_values[m]*100 if m in avg_stats and ref_values[m] else 0 for m in valid]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=norm_vals, theta=valid, fill='toself', name='Játékos'))
    fig.add_trace(go.Scatterpolar(r=[100]*len(valid), theta=valid, fill='toself', name='Benchmark'))
    fig.update_layout(title=title, polar=dict(radialaxis=dict(visible=True, range=[0, max(120, max(norm_vals, default=0))])))
    return fig

if uploaded_file:
    df = load_data(uploaded_file)
    df = df[df["Játékos neve"].notna()]

    st.sidebar.header("🎯 Szűrés")
    player_list = df["Játékos neve"].dropna().unique().tolist()
    selected_player = st.sidebar.selectbox("Játékos", player_list)
    tipus_list = df["Típus"].dropna().unique().tolist()
    selected_tipus = st.sidebar.selectbox("Típus", ["Összes"] + tipus_list)

    player_df = df[df["Játékos neve"] == selected_player]
    if selected_tipus != "Összes":
        player_df = player_df[player_df["Típus"] == selected_tipus]

    st.header(f"📌 {selected_player} játékos elemzése")

    ref_values = {
        "Teljes táv [m]": 5500,
        "Táv/perc [m/perc]": 100,
        "Max sebesség [km/h]": 30,
        "Sprintek száma": 25,
        "Zóna 5 gyorsulás": 10,
        "Zóna 5 lassulás": 10,
        "Zóna 5-6 táv": 500,
        "Izomterhelés": 65,
        "HRV (RMSSD)": 60,
        "Átlagos pulzus [bpm]": 160
    }

    mutatok_fizikai = ["Teljes táv [m]", "Táv/perc [m/perc]", "Max sebesség [km/h]", "Sprintek száma"]
    mutatok_terheles = ["Izomterhelés", "HRV (RMSSD)", "Átlagos pulzus [bpm]"]

    st.subheader("🕸️ Pókháló – Fizikai mutatók")
    radar1 = create_radar_chart(player_df, mutatok_fizikai, "Fizikai teljesítmény", ref_values)
    if radar1: st.plotly_chart(radar1, use_container_width=True)

    st.subheader("🕸️ Pókháló – Terhelés mutatók")
    radar2 = create_radar_chart(player_df, mutatok_terheles, "Terhelés és regeneráció", ref_values)
    if radar2: st.plotly_chart(radar2, use_container_width=True)

    st.subheader("📊 Táv, sebesség, sprint diagramok")
    cols = ["Teljes táv [m]", "Táv/perc [m/perc]", "Max sebesség [km/h]", "Sprintek száma"]
    available_cols = [col for col in cols if col in player_df.columns]
    if available_cols:
        fig_line = px.line(player_df, x="Forrás", y=available_cols, markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("📊 Izomterhelés és zónák")
    zones = ["Zóna 5 gyorsulás", "Zóna 5 lassulás", "Zóna 5-6 táv", "Izomterhelés"]
    valid_zones = [z for z in zones if z in player_df.columns]
    if valid_zones:
        fig_bar = px.bar(player_df, x="Forrás", y=valid_zones, barmode="group")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📈 HRV és pulzus trend")
    trends = ["HRV (RMSSD)", "Átlagos pulzus [bpm]"]
    valid_trends = [t for t in trends if t in player_df.columns]
    if valid_trends:
        fig_trend = px.line(player_df, x="Forrás", y=valid_trends, markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)

    st.subheader("🏆 Top10 játékos – Izomterhelés")
    if "Izomterhelés" in df.columns:
        top10 = df.groupby("Játékos neve")["Izomterhelés"].mean().sort_values(ascending=False).head(10).reset_index()
        fig_top10 = px.bar(top10, x="Izomterhelés", y="Játékos neve", orientation="h")
        st.plotly_chart(fig_top10, use_container_width=True)
else:
    st.info("Kérlek, tölts fel egy strukturált Excel fájlt az elemzéshez.")
