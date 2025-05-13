
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="Edzésterhelés Elemzés", layout="wide")
st.title("🏆 Heti edzésterhelés elemző alkalmazás")

# --- Fájl betöltés ---
uploaded_file = st.file_uploader("Tölts fel egy Excel fájlt (5 edzés + 1 meccs munkalappal)", type="xlsx")

@st.cache_data
def load_excel(file):
    excel = pd.ExcelFile(file)
    dfs = []
    for sheet in excel.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet)
        df["Forrás"] = sheet
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# --- Feldolgozás ---
def preprocess(df):
    df = df.copy()
    df = df[df["Játékos neve"].notna()]
    df["Kezdési idő"] = pd.to_datetime(df["Kezdési idő"], errors="coerce")
    df["Átlagos pulzus [bpm]"] = pd.to_numeric(df["Átlagos pulzus [bpm]"], errors="coerce")
    df["Izomterhelés"] = pd.to_numeric(df["Izomterhelés"], errors="coerce")
    df["HRV (RMSSD)"] = pd.to_numeric(df["HRV (RMSSD)"], errors="coerce")
    df["Időtartam"] = pd.to_timedelta(df["Időtartam"], errors="coerce")
    df["Időtartam perc"] = df["Időtartam"].dt.total_seconds() / 60
    df["Edzés/meccs"] = df["Forrás"].apply(lambda x: "Meccs" if "meccs" in x.lower() else "Edzés")
    return df

def calculate_summary(df):
    return df.groupby("Játékos neve").agg({
        "Átlagos pulzus [bpm]": "mean",
        "Izomterhelés": "sum",
        "HRV (RMSSD)": "mean",
        "Időtartam perc": "sum"
    }).rename(columns={
        "Átlagos pulzus [bpm]": "Átlagos pulzus",
        "Izomterhelés": "Összes izomterhelés",
        "HRV (RMSSD)": "Átlagos HRV",
        "Időtartam perc": "Össz idő (perc)"
    }).reset_index()

def plot_radar(player_data, avg_data, labels):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=player_data,
        theta=labels,
        fill='toself',
        name='Játékos'
    ))
    fig.add_trace(go.Scatterpolar(
        r=avg_data,
        theta=labels,
        fill='toself',
        name='Iparági átlag'
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True)
    return fig

# --- App logika ---
if uploaded_file:
    raw_df = load_excel(uploaded_file)
    df = preprocess(raw_df)

    st.sidebar.header("🎯 Szűrés")
    players = df["Játékos neve"].dropna().unique().tolist()
    selected_player = st.sidebar.selectbox("Válassz játékost", players)
    df_player = df[df["Játékos neve"] == selected_player]

    # Összefoglaló
    st.subheader("📊 Összesített mutatók")
    summary_df = calculate_summary(df)
    st.dataframe(summary_df)

    # Izomterhelés top 10
    st.subheader("🔥 Top 10 játékos izomterhelés szerint")
    top_df = summary_df.sort_values("Összes izomterhelés", ascending=False).head(10)
    fig_bar = px.bar(top_df, x="Játékos neve", y="Összes izomterhelés", title="Top 10 izomterhelés")
    st.plotly_chart(fig_bar, use_container_width=True)

    # HRV trend
    st.subheader("📈 HRV trend időben")
    fig_line = px.line(df_player, x="Kezdési idő", y="HRV (RMSSD)", markers=True, title=f"{selected_player} HRV trend")
    st.plotly_chart(fig_line, use_container_width=True)

    # Pókháló – egyszerűsített példa 5 mutatóval
    st.subheader("🕸️ Pókháló diagram – játékos vs iparági átlag")
    radar_labels = ["Pulzus", "Izomterhelés", "HRV", "Időtartam", "Táv/perc"]
    player_vals = [
        df_player["Átlagos pulzus [bpm]"].mean(),
        df_player["Izomterhelés"].sum(),
        df_player["HRV (RMSSD)"].mean(),
        df_player["Időtartam perc"].sum(),
        df_player["Időtartam perc"].sum() / len(df_player) if len(df_player) > 0 else 0
    ]
    industry_vals = [160, 70, 60, 80, 120]  # példaként iparági átlag
    fig_radar = plot_radar(player_vals, industry_vals, radar_labels)
    st.plotly_chart(fig_radar, use_container_width=True)

else:
    st.info("Tölts fel egy Excel fájlt az elemzéshez.")
