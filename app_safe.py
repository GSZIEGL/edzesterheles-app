
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

def safe_convert(df, col):
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def preprocess(df):
    df = df[df["Játékos neve"].notna()].copy()
    df["Kezdési idő"] = pd.to_datetime(df["Kezdési idő"], errors="coerce")
    cols_to_convert = [
        "Átlagos pulzus [bpm]", "Izomterhelés", "HRV (RMSSD)",
        "Max sebesség [km/h]", "Sprintek száma", "Zóna 5 gyorsulás",
        "Zóna 5 lassulás", "Zóna 5-6 táv"
    ]
    for col in cols_to_convert:
        df = safe_convert(df, col)

    if "Időtartam" in df.columns:
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
    selected_cols = [
        "Átlagos pulzus [bpm]", "Izomterhelés", "HRV (RMSSD)",
        "Max sebesség [km/h]", "Sprintek száma", "Zóna 5 gyorsulás",
        "Zóna 5 lassulás", "Zóna 5-6 táv"
    ]
    available_cols = [col for col in selected_cols if col in df_player.columns]
    agg = df_player[available_cols].agg("mean").to_frame().T
    st.dataframe(agg)

    if len(available_cols) >= 3:
        st.subheader("🕸️ Pókháló diagram – játékos vs iparági átlag")
        radar_labels = available_cols
        player_vals = [agg[col].values[0] for col in radar_labels]
        industry_vals = [160, 70, 60, 32, 30, 15, 15, 500][:len(radar_labels)]
        radar_fig = plot_radar(player_vals, industry_vals, radar_labels)
        st.plotly_chart(radar_fig, use_container_width=True)

else:
    st.info("Tölts fel egy Excel fájlt az elemzéshez.")
