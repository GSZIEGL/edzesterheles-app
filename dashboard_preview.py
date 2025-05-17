
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Edzésterhelés Dashboard – Előnézet", layout="wide")
st.title("📊 Előnézeti verzió – Teljes Edzésterhelés Dashboard")

uploaded_file = st.file_uploader("Tölts fel egy Excel fájlt (6 sheet: 5 edzés + 1 meccs)", type="xlsx")

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    dfs = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["Forrás"] = sheet
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

if uploaded_file:
    df = load_data(uploaded_file)
    df = df[df["Játékos neve"].notna()]

    st.sidebar.header("Szűrés")
    player = st.sidebar.selectbox("Játékos kiválasztása", df["Játékos neve"].unique())
    tipusok = df["Típus"].dropna().unique()
    selected_tipus = st.sidebar.selectbox("Típus szűrés", ["Összes"] + list(tipusok))

    df_player = df[df["Játékos neve"] == player]
    if selected_tipus != "Összes":
        df_player = df_player[df_player["Típus"] == selected_tipus]

    st.subheader(f"Átlagolt mutatók – {player}")
    mutatok = ["Teljes táv [m]", "Táv/perc [m/perc]", "Max sebesség [km/h]", "Sprintek száma",
               "Izomterhelés", "HRV (RMSSD)", "Átlagos pulzus [bpm]"]
    ref = {"Teljes táv [m]": 5500, "Táv/perc [m/perc]": 100, "Max sebesség [km/h]": 30,
           "Sprintek száma": 25, "Izomterhelés": 65, "HRV (RMSSD)": 60, "Átlagos pulzus [bpm]": 160}

    valid = [m for m in mutatok if m in df_player.columns]
    if valid:
        values = df_player[valid].mean()
        radar_vals = [values[v]/ref[v]*100 for v in valid]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=radar_vals, theta=valid, fill='toself', name=player))
        fig.add_trace(go.Scatterpolar(r=[100]*len(valid), theta=valid, fill='toself', name="Iparági átlag"))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(120, max(radar_vals))])))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top10 játékos – Izomterhelés")
    if "Izomterhelés" in df.columns:
        top10 = df.groupby("Játékos neve")["Izomterhelés"].mean().sort_values(ascending=False).head(10).reset_index()
        bar = px.bar(top10, x="Izomterhelés", y="Játékos neve", orientation="h", title="Top10 Izomterhelés")
        st.plotly_chart(bar, use_container_width=True)
else:
    st.info("Tölts fel egy adatfájlt az előnézethez.")
