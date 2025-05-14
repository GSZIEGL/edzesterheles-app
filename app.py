
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="Edzésterhelés Elemzés", layout="wide")
st.title("🏆 Heti edzésterhelés elemző alkalmazás")

uploaded_file = st.file_uploader("📤 Excel fájl feltöltése (5 edzés + 1 meccs munkalappal)", type="xlsx")

@st.cache_data
def load_excel(file):
    excel = pd.ExcelFile(file)
    dfs = []
    for sheet in excel.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet)
        df["Forrás"] = sheet
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

def preprocess(df):
    df = df[df["Játékos neve"].notna()].copy()
    df["Kezdési idő"] = pd.to_datetime(df["Kezdési idő"], errors="coerce")
    df["Átlagos pulzus [bpm]"] = pd.to_numeric(df["Átlagos pulzus [bpm]"], errors="coerce")
    df["Izomterhelés"] = pd.to_numeric(df["Izomterhelés"], errors="coerce")
    df["HRV (RMSSD)"] = pd.to_numeric(df["HRV (RMSSD)"], errors="coerce")
    df["Max sebesség [km/h]"] = pd.to_numeric(df["Max sebesség [km/h]"], errors="coerce")
    df["Sprintek száma"] = pd.to_numeric(df["Sprintek száma"], errors="coerce")
    df["Zóna 5 gyorsulás"] = pd.to_numeric(df["Zóna 5 gyorsulás"], errors="coerce")
    df["Zóna 5 lassulás"] = pd.to_numeric(df["Zóna 5 lassulás"], errors="coerce")
    df["Zóna 5-6 táv"] = pd.to_numeric(df["Zóna 5-6 táv"], errors="coerce")
    df["Időtartam"] = pd.to_timedelta(df["Időtartam"], errors="coerce")
    df["Időtartam perc"] = df["Időtartam"].dt.total_seconds() / 60
    return df

def plot_radar(player_data, avg_data, labels):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=player_data, theta=labels, fill='toself', name='Játékos'))
    fig.add_trace(go.Scatterpolar(r=avg_data, theta=labels, fill='toself', name='Iparági átlag'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True)
    return fig

if uploaded_file:
    raw_df = load_excel(uploaded_file)
    df = preprocess(raw_df)

    st.sidebar.header("🎯 Szűrés")
    players = df["Játékos neve"].dropna().unique().tolist()
    selected_player = st.sidebar.selectbox("Játékos kiválasztása", players)

    df_player = df[df["Játékos neve"] == selected_player]

    st.subheader("📊 Összesített mutatók")
    agg = df_player.agg({
        "Átlagos pulzus [bpm]": "mean",
        "Izomterhelés": "sum",
        "HRV (RMSSD)": "mean",
        "Max sebesség [km/h]": "max",
        "Sprintek száma": "sum",
        "Zóna 5 gyorsulás": "sum",
        "Zóna 5 lassulás": "sum",
        "Zóna 5-6 táv": "sum"
    }).to_frame().T
    st.dataframe(agg)

    st.subheader("🕸️ Pókháló diagram – játékos vs iparági átlag")
    radar_labels = ["Pulzus", "Izomterhelés", "HRV", "Max sebesség", "Sprintek", "Gyorsulás", "Lassulás", "Zóna 5-6 táv"]
    player_vals = [
        agg["Átlagos pulzus [bpm]"].values[0],
        agg["Izomterhelés"].values[0],
        agg["HRV (RMSSD)"].values[0],
        agg["Max sebesség [km/h]"].values[0],
        agg["Sprintek száma"].values[0],
        agg["Zóna 5 gyorsulás"].values[0],
        agg["Zóna 5 lassulás"].values[0],
        agg["Zóna 5-6 táv"].values[0]
    ]
    industry_vals = [160, 70, 60, 32, 30, 15, 15, 500]  # példa iparági referencia
    radar_fig = plot_radar(player_vals, industry_vals, radar_labels)
    st.plotly_chart(radar_fig, use_container_width=True)

else:
    st.info("Tölts fel egy Excel fájlt az elemzéshez.")
