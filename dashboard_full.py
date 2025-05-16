
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Teljes edzésterhelés elemzés", layout="wide")
st.title("📊 Teljes edzésterhelés és meccsterhelés dashboard")

uploaded_file = st.file_uploader("📤 Excel fájl feltöltése (6 munkalappal: 5 edzés + 1 meccs)", type="xlsx")

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    all_dfs = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet)
        df["Forrás"] = sheet
        all_dfs.append(df)
    return pd.concat(all_dfs, ignore_index=True)

def normalize(val, ref):
    return val / ref * 100 if ref else 0

if uploaded_file:
    df = load_data(uploaded_file)
    df = df[df["Játékos neve"].notna()].copy()

    st.sidebar.header("🎯 Szűrők")
    players = df["Játékos neve"].dropna().unique().tolist()
    selected_player = st.sidebar.selectbox("Játékos kiválasztása", players)

    player_df = df[df["Játékos neve"] == selected_player]

    st.subheader("📋 Összesített mutatók (átlagolva)")
    numeric_cols = ["Teljes táv [m]", "Táv/perc [m/perc]", "HRV (RMSSD)", "Átlagos pulzus [bpm]",
                    "Max sebesség [km/h]", "Izomterhelés", "Sprintek száma",
                    "Zóna 5 gyorsulás", "Zóna 5 lassulás", "Zóna 5-6 táv"]
    ref_values = {
        "Teljes táv [m]": 5500, "Táv/perc [m/perc]": 100, "HRV (RMSSD)": 60, "Átlagos pulzus [bpm]": 160,
        "Max sebesség [km/h]": 30, "Izomterhelés": 65, "Sprintek száma": 25,
        "Zóna 5 gyorsulás": 10, "Zóna 5 lassulás": 10, "Zóna 5-6 táv": 500
    }

    available_cols = [col for col in numeric_cols if col in player_df.columns]
    player_stats = player_df[available_cols].mean()

    df_normalized = [normalize(player_stats[col], ref_values[col]) for col in available_cols]

    radar_fig = go.Figure()
    radar_fig.add_trace(go.Scatterpolar(r=df_normalized, theta=available_cols, fill='toself', name=selected_player))
    radar_fig.add_trace(go.Scatterpolar(r=[100]*len(df_normalized), theta=available_cols, fill='toself', name='Iparági átlag'))
    radar_fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(120, max(df_normalized))])), showlegend=True)

    st.plotly_chart(radar_fig, use_container_width=True)

    st.subheader("📈 Trend diagram: HRV és Pulzus alakulása")
    if "Kezdési idő" in player_df.columns:
        player_df["Kezdési idő"] = pd.to_datetime(player_df["Kezdési idő"], errors="coerce")
        fig = px.line(player_df.sort_values("Kezdési idő"), x="Kezdési idő", y=["HRV (RMSSD)", "Átlagos pulzus [bpm]"],
                      markers=True, labels={"value": "Érték", "Kezdési idő": "Dátum", "variable": "Mutató"})
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("🏃‍♂️ Sebesség és sprint diagram")
    if "Sprintek száma" in player_df.columns and "Max sebesség [km/h]" in player_df.columns:
        sprint_fig = px.bar(player_df, x="Forrás", y="Sprintek száma", color="Max sebesség [km/h]",
                            labels={"Forrás": "Edzés/Meccs", "Sprintek száma": "Sprintek", "Max sebesség [km/h]": "Max seb."})
        st.plotly_chart(sprint_fig, use_container_width=True)

    st.subheader("🏁 Izomterhelés és zónák")
    zone_cols = [col for col in ["Zóna 5 gyorsulás", "Zóna 5 lassulás", "Zóna 5-6 táv", "Izomterhelés"] if col in player_df.columns]
    if zone_cols:
        zone_fig = px.bar(player_df, x="Forrás", y=zone_cols, barmode="group")
        st.plotly_chart(zone_fig, use_container_width=True)
else:
    st.info("Tölts fel egy megfelelő struktúrájú Excel fájlt (6 munkalap: 5 edzés + 1 meccs).")
