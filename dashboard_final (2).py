
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Edzésterhelés Dashboard", layout="wide")
st.title("📊 Edzés- és Meccsterhelés Elemző Dashboard")

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
    player_names = df["Játékos neve"].unique().tolist()
    selected_player = st.sidebar.selectbox("Játékos kiválasztása", player_names)

    df_player = df[df["Játékos neve"] == selected_player]

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

    available_mutatok = [m for m in mutatok if m in df_player.columns]
    if available_mutatok:
        st.subheader("🕸️ Pókháló diagram – Játékos vs Iparági Átlag")
        avg_stats = df_player[available_mutatok].mean()
        norm_vals = [normalize(avg_stats[col], ref[col]) for col in available_mutatok]
        radar = go.Figure()
        radar.add_trace(go.Scatterpolar(r=norm_vals, theta=available_mutatok, fill='toself', name=selected_player))
        radar.add_trace(go.Scatterpolar(r=[100]*len(norm_vals), theta=available_mutatok, fill='toself', name='Iparági átlag'))
        radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(120, max(norm_vals))])), showlegend=True)
        st.plotly_chart(radar, use_container_width=True)

    if "Kezdési idő" in df_player.columns and "HRV (RMSSD)" in df_player.columns and "Átlagos pulzus [bpm]" in df_player.columns:
        st.subheader("📈 HRV és Pulzus trendje")
        df_player["Kezdési idő"] = pd.to_datetime(df_player["Kezdési idő"], errors="coerce")
        fig = px.line(df_player.sort_values("Kezdési idő"), x="Kezdési idő",
                      y=["HRV (RMSSD)", "Átlagos pulzus [bpm]"], markers=True)
        st.plotly_chart(fig, use_container_width=True)

    if "Sprintek száma" in df_player.columns and "Max sebesség [km/h]" in df_player.columns:
        st.subheader("🏃‍♂️ Sprintek és Max Sebesség")
        fig2 = px.bar(df_player, x="Forrás", y="Sprintek száma", color="Max sebesség [km/h]",
                      labels={"Forrás": "Edzés/Meccs"})
        st.plotly_chart(fig2, use_container_width=True)

    zone_cols = [col for col in ["Zóna 5 gyorsulás", "Zóna 5 lassulás", "Zóna 5-6 táv", "Izomterhelés"] if col in df_player.columns]
    if zone_cols:
        st.subheader("📦 Zóna és Izomterhelés mutatók")
        fig3 = px.bar(df_player, x="Forrás", y=zone_cols, barmode="group")
        st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Tölts fel egy megfelelő Excel fájlt (5 edzés + 1 meccs sheettel).")
