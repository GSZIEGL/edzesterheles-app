
# Edzésterhelés App – Végleges verzió
# Funkciók: több játékos, pizza, benchmark, trend, típus, heti összehasonlítás, tárolt adatok, focis design

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="⚽ Edzésterhelés Dashboard", layout="wide")

st.markdown("## ⚽ Edzésterhelés – Komplex Elemző Rendszer")
st.markdown("Interaktív elemzés játékosok, hetek és mutatók szerint, benchmarkkal és csapatátlaggal összevetve.")

if "df_all" not in st.session_state:
    st.session_state["df_all"] = pd.DataFrame()

uploaded_file = st.file_uploader("📥 Új heti adat feltöltése (Excel, külön munkalapok)", type="xlsx")

@st.cache_data
def load_excel(file):
    xls = pd.ExcelFile(file)
    all_sheets = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["Hét"] = sheet
        all_sheets.append(df)
    return pd.concat(all_sheets, ignore_index=True)

def normalize_series(s):
    return (s - s.min()) / (s.max() - s.min()) * 100 if s.max() != s.min() else s

def add_to_session(df_new):
    if not st.session_state["df_all"].empty:
        st.session_state["df_all"] = pd.concat([st.session_state["df_all"], df_new], ignore_index=True)
    else:
        st.session_state["df_all"] = df_new

if uploaded_file:
    df_new = load_excel(uploaded_file)
    add_to_session(df_new)

df = st.session_state["df_all"]

if not df.empty:
    df = df[df["Játékos neve"].notna()]
    all_metrics = [c for c in df.columns if df[c].dtype in ["float64", "int64"] and c not in ["Kor", "Évfolyam"]]
    all_players = sorted(df["Játékos neve"].dropna().unique().tolist())
    all_types = sorted(df["Típus"].dropna().unique().tolist())
    all_weeks = sorted(df["Hét"].dropna().unique().tolist())

    st.sidebar.header("🎛 Szűrőpanel")

    with st.sidebar.expander("🧍‍♂️ Játékosok"):
        selected_players = st.multiselect("Válassz játékosokat", all_players, default=all_players[:1])

    with st.sidebar.expander("🏷 Típus és Hét"):
        selected_type = st.selectbox("Típus", ["Összes"] + all_types)
        selected_weeks = st.multiselect("Hetek", all_weeks, default=all_weeks)

    with st.sidebar.expander("📊 Mutatók"):
        selected_metrics = st.multiselect("Mutatók", all_metrics)

    df_filtered = df[df["Játékos neve"].isin(selected_players)]
    if selected_type != "Összes":
        df_filtered = df_filtered[df_filtered["Típus"] == selected_type]
    df_filtered = df_filtered[df_filtered["Hét"].isin(selected_weeks)]

    df_team = df[df["Hét"].isin(selected_weeks)]
    if selected_type != "Összes":
        df_team = df_team[df_team["Típus"] == selected_type]

    st.markdown("### 📊 Összehasonlítás – játékos vs csapat vs benchmark")

    ref_values = {
        "Teljes táv [m]": 5500,
        "Táv/perc [m/perc]": 100,
        "Max sebesség [km/h]": 30,
        "Sprintek száma": 25,
        "Izomterhelés": 65,
        "HRV (RMSSD)": 60,
        "Átlagos pulzus [bpm]": 160,
        "Zóna 5-6 táv": 500,
        "Zóna 5 gyorsulás": 10,
        "Zóna 5 lassulás": 10
    }

    if selected_metrics:
        chart_data = []
        for mut in selected_metrics:
            chart_data.append({
                "Mutató": mut,
                "Játékos": df_filtered[mut].mean() if mut in df_filtered else None,
                "Csapat": df_team[mut].mean() if mut in df_team else None,
                "Benchmark": ref_values.get(mut, None)
            })
        comp_df = pd.DataFrame(chart_data)
        fig_bar = px.bar(comp_df, x="Mutató", y=["Játékos", "Csapat", "Benchmark"], barmode="group")
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("### 🍕 Pizzadiagram(ok)")
        for player in selected_players:
            df_p = df_filtered[df_filtered["Játékos neve"] == player]
            if df_p.empty:
                continue
            pizza_df = df_p[selected_metrics].mean().dropna().reset_index()
            pizza_df.columns = ["Mutató", "Érték"]
            pizza_df["Benchmark"] = pizza_df["Mutató"].map(ref_values)
            fig_pizza = px.bar_polar(pizza_df, r="Érték", theta="Mutató", title=f"{player} pizza diagram", range_r=[0, pizza_df["Benchmark"].max()*1.2])
            st.plotly_chart(fig_pizza, use_container_width=True)

        st.markdown("### 📈 Normalizált trenddiagram (játékosok átlaga)")
        df_trend = df_filtered.groupby(["Hét"])[selected_metrics].mean().reset_index()
        for col in selected_metrics:
            if col in df_trend.columns:
                df_trend[col] = normalize_series(df_trend[col])
        fig_line = px.line(df_trend, x="Hét", y=selected_metrics, markers=True, title="Normalizált trendmutatók")
        st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("### 📋 Benchmark táblázat")
        st.dataframe(pd.DataFrame.from_dict(ref_values, orient="index", columns=["Benchmark értékek"]).reset_index().rename(columns={"index": "Mutató"}))

    st.markdown("### 📂 Szűrt adattábla")
    st.dataframe(df_filtered[selected_metrics + ["Játékos neve", "Hét", "Típus"]] if selected_metrics else df_filtered)
else:
    st.info("Tölts fel legalább egy heti adatot az elemzéshez.")
