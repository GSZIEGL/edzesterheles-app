
# Végleges Edzésterhelés Dashboard – Benchmark, Pizza, Trend, Kombinált Ábrák

import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="⚽ Edzésterhelés Dashboard", layout="wide")

st.title("⚽ Edzésterhelés – Teljes Elemző Rendszer")

DATA_FILE = "saved_data.csv"

@st.cache_data
def load_excel(file):
    xls = pd.ExcelFile(file)
    all_sheets = []
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

# === Benchmark értékek (példák, bővíthető) ===
benchmark_nominal = {
    "Teljes táv [m]": 5500,
    "Táv/perc [m/perc]": 110,
    "Max sebesség [km/h]": 30,
    "Sprintek száma": 25,
    "Izomterhelés": 70,
    "HRV (RMSSD)": 60,
    "Átlagos pulzus [bpm]": 160,
    "Zóna 5-6 táv": 400,
    "Zóna 5 gyorsulás": 10,
    "Zóna 5 lassulás": 10
}
benchmark_relative = {
    "Teljes táv [m]": 2.5,
    "Táv/perc [m/perc]": 0.7,
    "Zóna 4-5 táv": 1.5
}

uploaded_file = st.file_uploader("📥 Heti Excel feltöltése", type="xlsx")

if uploaded_file:
    df_new = load_excel(uploaded_file)
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

    df_filtered = df_all[df_all["Játékos neve"].isin(selected_players)]
    if selected_type != "Összes":
        df_filtered = df_filtered[df_filtered["Típus"] == selected_type]
    df_filtered = df_filtered[df_filtered["Hét"].isin(selected_weeks)]

    df_team = df_all[df_all["Hét"].isin(selected_weeks)]
    if selected_type != "Összes":
        df_team = df_team[df_team["Típus"] == selected_type]

    st.header("📊 Összehasonlító diagram: Játékos(ok) vs Csapat vs Benchmark")
    if selected_metrics:
        summary = []
        for mut in selected_metrics:
            summary.append({
                "Mutató": mut,
                "Játékos": df_filtered[mut].mean(),
                "Csapat": df_team[mut].mean(),
                "Benchmark": benchmark_nominal.get(mut)
            })
        df_summary = pd.DataFrame(summary)
        st.plotly_chart(px.bar(df_summary, x="Mutató", y=["Játékos", "Csapat", "Benchmark"], barmode="group"), use_container_width=True)

    st.header("🍕 Pizzadiagram(ok)")
    if pizza_mode == "Egy diagram több játékossal":
        pizza_data = []
        for player in selected_players:
            df_p = df_filtered[df_filtered["Játékos neve"] == player]
            if not df_p.empty:
                row = df_p[selected_metrics].mean().to_dict()
                row["Játékos"] = player
                pizza_data.append(row)
        df_pizza = pd.DataFrame(pizza_data)
        df_pizza = df_pizza.melt(id_vars="Játékos", var_name="Mutató", value_name="Érték")
        fig = px.line_polar(df_pizza, r="Érték", theta="Mutató", color="Játékos", line_close=True, range_r=[0, df_pizza["Érték"].max()*1.1])
        st.plotly_chart(fig, use_container_width=True)
    else:
        for player in selected_players:
            st.subheader(f"{player}")
            df_p = df_filtered[df_filtered["Játékos neve"] == player]
            if not df_p.empty:
                pizza_df = df_p[selected_metrics].mean().dropna().reset_index()
                pizza_df.columns = ["Mutató", "Érték"]
                fig = px.bar_polar(pizza_df, r="Érték", theta="Mutató", range_r=[0, pizza_df["Érték"].max()*1.1], title=f"{player}")
                st.plotly_chart(fig, use_container_width=True)

    st.header("📈 Trenddiagram (normalizált)")
    trend_df = df_filtered.groupby("Hét")[selected_metrics].mean().reset_index()
    for m in selected_metrics:
        if m in trend_df.columns:
            trend_df[m] = normalize_series(trend_df[m])
    st.plotly_chart(px.line(trend_df, x="Hét", y=selected_metrics, markers=True), use_container_width=True)

    st.header("📋 Benchmark táblázat és viszonyítás")
    bench_table = []
    for mut in selected_metrics:
        bench = benchmark_nominal.get(mut)
        edzes_avg = df_filtered[df_filtered["Típus"] == "Edzés"][mut].mean()
        meccs_avg = df_filtered[df_filtered["Típus"] == "Meccs"][mut].mean()
        if pd.notna(meccs_avg) and meccs_avg != 0:
            arany = edzes_avg / meccs_avg
        else:
            arany = None
        elvart = benchmark_relative.get(mut)
        teljesites = arany / elvart * 100 if elvart and arany else None
        bench_table.append({
            "Mutató": mut,
            "Meccs átlag": meccs_avg,
            "Edzés átlag": edzes_avg,
            "Benchmark cél (meccs szorzó)": elvart,
            "Tényleges arány": arany,
            "Teljesítés (%)": teljesites
        })
    st.dataframe(pd.DataFrame(bench_table))
else:
    st.info("📥 Tölts fel heti adatot az elemzéshez (Excel fájl)")
