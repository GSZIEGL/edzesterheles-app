
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Végső Edzésterhelés Dashboard", layout="wide")
st.title("📊 Edzésterhelés és Meccsterhelés – Teljes Dashboard")

uploaded_file = st.file_uploader("📤 Tölts fel egy Excel fájlt (6 sheet: 5 edzés + 1 meccs)", type="xlsx")

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    dfs = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["Forrás"] = sheet
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

def normalize(val, ref):
    return val / ref * 100 if ref else 0

if uploaded_file:
    df = load_data(uploaded_file)
    df = df[df["Játékos neve"].notna()]
    st.sidebar.header("🎯 Szűrés")
    player = st.sidebar.selectbox("Játékos kiválasztása", df["Játékos neve"].unique())
    tipusok = df["Típus"].dropna().unique().tolist()
    tipus = st.sidebar.selectbox("Típus szűrés", ["Összes"] + tipusok)
    if tipus != "Összes":
        df = df[df["Típus"] == tipus]
    df_player = df[df["Játékos neve"] == player]

    mutatok = [
        "Teljes táv [m]",
        "Táv/perc [m/perc]",
        "Max sebesség [km/h]",
        "Sprintek száma",
        "Zóna 5 gyorsulás",
        "Zóna 5 lassulás",
        "Zóna 5-6 táv",
        "Izomterhelés",
        "HRV (RMSSD)",
        "Átlagos pulzus [bpm]"
    ]
    ref = {
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

    available = [m for m in mutatok if m in df_player.columns]
    if available:
        st.subheader("🕸️ Pókháló – Játékos vs Benchmark")
        avg_vals = df_player[available].mean()
        scaled = [normalize(avg_vals[m], ref[m]) for m in available]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=scaled, theta=available, fill='toself', name=player))
        fig.add_trace(go.Scatterpolar(r=[100]*len(scaled), theta=available, fill='toself', name='Iparági átlag'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(120, max(scaled))])))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("🏃‍♂️ Sprintek és Max Sebesség")
    if "Sprintek száma" in df_player.columns:
        fig2 = px.bar(df_player, x="Forrás", y="Sprintek száma", color="Max sebesség [km/h]")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📦 Zóna és Izomterhelés")
    zones = ["Zóna 5 gyorsulás", "Zóna 5 lassulás", "Zóna 5-6 táv", "Izomterhelés"]
    valid_zones = [z for z in zones if z in df_player.columns]
    if valid_zones:
        fig3 = px.bar(df_player, x="Forrás", y=valid_zones, barmode="group")
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("🏆 Top10 Izomterhelés")
    if "Izomterhelés" in df.columns:
        top10 = df.groupby("Játékos neve")["Izomterhelés"].mean().sort_values(ascending=False).head(10).reset_index()
        fig4 = px.bar(top10, x="Izomterhelés", y="Játékos neve", orientation="h")
        st.plotly_chart(fig4, use_container_width=True)

else:
    st.info("Tölts fel egy strukturált Excel fájlt az elemzéshez.")
