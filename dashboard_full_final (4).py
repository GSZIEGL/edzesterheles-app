
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Edzésterhelés Dashboard", layout="wide")
st.title("⚽ Teljes edzésterhelés elemzés – Végleges verzió")

uploaded_file = st.file_uploader("📤 Tölts fel egy Excel fájlt (5 edzés + 1 meccs munkalap)", type="xlsx")

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    df_list = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["Forrás"] = sheet
        df_list.append(df)
    return pd.concat(df_list, ignore_index=True)

def create_radar(player_df, title, ref_values, mutatok):
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
    selected_player = st.sidebar.selectbox("Válassz játékost", player_list)
    tipus_list = df["Típus"].dropna().unique().tolist()
    selected_tipus = st.sidebar.selectbox("Válassz típust", ["Összes"] + tipus_list)

    player_df = df[df["Játékos neve"] == selected_player]
    if selected_tipus != "Összes":
        player_df = player_df[player_df["Típus"] == selected_tipus]

    st.header(f"📌 Elemzés – {selected_player}")
    ref_values = {
        "Teljes táv [m]": 5500,
        "Táv/perc [m/perc]": 100,
        "Max sebesség [km/h]": 30,
        "Sprintek száma": 25,
        "Izomterhelés": 65,
        "HRV (RMSSD)": 60,
        "Átlagos pulzus [bpm]": 160
    }

    mutatok_1 = ["Teljes táv [m]", "Táv/perc [m/perc]", "Max sebesség [km/h]", "Sprintek száma"]
    mutatok_2 = ["Izomterhelés", "HRV (RMSSD)", "Átlagos pulzus [bpm]"]

    radar1 = create_radar(player_df, "Fizikai teljesítmény", ref_values, mutatok_1)
    radar2 = create_radar(player_df, "Terhelés és regeneráció", ref_values, mutatok_2)

    if radar1:
        st.subheader("🕸️ Pókháló – Fizikai mutatók")
        st.plotly_chart(radar1, use_container_width=True)
    if radar2:
        st.subheader("🕸️ Pókháló – Terhelés mutatók")
        st.plotly_chart(radar2, use_container_width=True)

    if "Sprintek száma" in player_df.columns:
        st.subheader("🏃‍♂️ Sprintek száma edzésenként")
        sprint_fig = px.bar(player_df, x="Forrás", y="Sprintek száma", title="Sprintek száma")
        st.plotly_chart(sprint_fig, use_container_width=True)

    if "Izomterhelés" in df.columns:
        st.subheader("🏆 Top10 játékos – Izomterhelés (átlag)")
        top_df = df.groupby("Játékos neve")["Izomterhelés"].mean().sort_values(ascending=False).head(10).reset_index()
        top_fig = px.bar(top_df, x="Izomterhelés", y="Játékos neve", orientation="h")
        st.plotly_chart(top_fig, use_container_width=True)
else:
    st.info("Kérlek, tölts fel egy 6 munkalapos Excel fájlt (5 edzés, 1 meccs).")
