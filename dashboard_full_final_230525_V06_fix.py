
# ⚽ Edzésterhelés Dashboard V06_fix – gyorsjavított változat
# ✅ Benchmark eltávolítva a pizzáról
# ✅ Trenddiagram működik
# ✅ Alapértelmezett benchmark minden mutatóhoz
# ✅ Hetek külön szűrhetők

import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="⚽ Edzésterhelés Dashboard", layout="wide")
st.title("⚽ Edzésterhelés – Gyorsjavított Változat (V06_fix)")

DATA_FILE = "saved_data.csv"

@st.cache_data
def load_excel(files):
    all_sheets = []
    for file in files:
        xls = pd.ExcelFile(file)
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df["Hét"] = sheet
            all_sheets.append(df)
    return pd.concat(all_sheets, ignore_index=True)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def load_saved_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame()

def append_data(new_df, saved_df):
    combined = pd.concat([saved_df, new_df], ignore_index=True)
    combined.drop_duplicates(inplace=True)
    return combined

def normalize_series(s):
    return (s - s.min()) / (s.max() - s.min()) * 100 if s.max() != s.min() else s

# Alap benchmark dummy értékek minden mutatóhoz
benchmark_nominal = {k: 100 for k in [
    "Teljes táv [m]", "Táv/perc [m/perc]", "Max sebesség [km/h]", "Sprintek száma",
    "Izomterhelés", "HRV (RMSSD)", "Átlagos pulzus [bpm]", "Zóna 5-6 táv",
    "Zóna 5 gyorsulás", "Zóna 5 lassulás"
]}

uploaded_files = st.file_uploader("📥 Heti Excel(ek) feltöltése", type="xlsx", accept_multiple_files=True)

if uploaded_files:
    df_new = load_excel(uploaded_files)
    df_old = load_saved_data()
    df_all = append_data(df_new, df_old)
    save_data(df_all)
else:
    df_all = load_saved_data()

if not df_all.empty:
    df_all = df_all[df_all["Játékos neve"].notna()]
    mutatok = [c for c in df_all.columns if df_all[c].dtype in ["float64", "int64"] and c not in ["Kor", "Évfolyam"]]
    all_players = sorted(df_all["Játékos neve"].dropna().unique())
    all_types = sorted(df_all["Típus"].dropna().unique())
    all_weeks = sorted(df_all["Hét"].dropna().unique())

    st.sidebar.header("🎛 Szűrők")
    selected_players = st.sidebar.multiselect("Játékos(ok)", all_players, default=all_players[:1])
    selected_type = st.sidebar.selectbox("Típus", ["Összes"] + all_types)
    selected_weeks = st.sidebar.multiselect("Hetek", all_weeks, default=all_weeks)
    selected_metrics = st.sidebar.multiselect("Mutatók", mutatok)
    pizza_mode = st.sidebar.radio("Pizzadiagram mód", ["Egy diagram több játékossal", "Külön pizzák játékosonként"])
    show_team_avg = st.sidebar.checkbox("Mutasd a csapatátlagot a pizzán")

    df_filtered = df_all[df_all["Játékos neve"].isin(selected_players)]
    if selected_type != "Összes":
        df_filtered = df_filtered[df_filtered["Típus"] == selected_type]
    df_filtered = df_filtered[df_filtered["Hét"].isin(selected_weeks)]

    df_team = df_all[df_all["Hét"].isin(selected_weeks)]
    if selected_type != "Összes":
        df_team = df_team[df_team["Típus"] == selected_type]

    st.header("📊 Összehasonlító diagram: Játékos(ok) vs Csapat")
    if selected_metrics:
        summary = []
        for mut in selected_metrics:
            for player in selected_players:
                val = df_filtered[df_filtered["Játékos neve"] == player][mut].mean()
                summary.append({"Mutató": mut, "Név": player, "Érték": val})
            summary.append({"Mutató": mut, "Név": "Csapatátlag", "Érték": df_team[mut].mean()})
        df_summary = pd.DataFrame(summary)
        fig = px.bar(df_summary, x="Mutató", y="Érték", color="Név", barmode="group")
        st.plotly_chart(fig, use_container_width=True)

    st.header("🍕 Pizzadiagram(ok)")
    pizza_data = []
    for player in selected_players:
        df_p = df_filtered[df_filtered["Játékos neve"] == player]
        if not df_p.empty:
            row = df_p[selected_metrics].mean().to_dict()
            row["Játékos"] = player
            pizza_data.append(row)

    if show_team_avg:
        team_row = df_team[selected_metrics].mean().to_dict()
        team_row["Játékos"] = "Csapatátlag"
        pizza_data.append(team_row)

    df_pizza = pd.DataFrame(pizza_data)
    df_pizza = df_pizza.melt(id_vars="Játékos", var_name="Mutató", value_name="Érték")
    max_val = df_pizza["Érték"].max()
    if pizza_mode == "Egy diagram több játékossal":
        fig = px.line_polar(df_pizza, r="Érték", theta="Mutató", color="Játékos", line_close=True, range_r=[0, max_val*1.1])
        st.plotly_chart(fig, use_container_width=True)
    else:
        for player in df_pizza["Játékos"].unique():
            st.subheader(f"{player}")
            subset = df_pizza[df_pizza["Játékos"] == player]
            fig = px.bar_polar(subset, r="Érték", theta="Mutató", range_r=[0, max_val*1.1], title=player)
            st.plotly_chart(fig, use_container_width=True)

    st.header("📈 Trenddiagramok")
    for player in selected_players:
        st.subheader(f"{player}")
        player_df = df_filtered[df_filtered["Játékos neve"] == player]
        if not player_df.empty:
            trend_df = player_df.groupby("Hét")[selected_metrics].mean().reset_index()
            for m in selected_metrics:
                if m in trend_df.columns:
                    trend_df[m] = normalize_series(trend_df[m])
            fig = px.line(trend_df, x="Hét", y=selected_metrics, markers=True, title=player)
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("📥 Tölts fel heti adatot az elemzéshez (Excel fájl)")
