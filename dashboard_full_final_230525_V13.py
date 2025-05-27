
# ⚽ V13 – végleges, működő Streamlit alkalmazás

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")
st.title("⚽ Edzésterhelés – V13")

BENCHMARK_ARANY = {
    "Teljes táv [m]": 2.5,
    "Táv/perc [m/min]": 0.7,
    "Táv zóna 4 [m]": 1.5,
    "Táv zóna 5 [m]": 1.5,
    "Sprint szám": 2.0,
    "Gyorsulások száma": 1.5,
    "Lassítások száma": 1.5,
    "Izomterhelés": 2.5,
    "Edzésterhelés": 3.0,
    "Max sebesség [km/h]": 1.0
}

uploaded_files = st.file_uploader("📁 Excel fájl(ok) feltöltése", type="xlsx", accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for file in uploaded_files:
        xls = pd.ExcelFile(file)
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df["Hét"] = sheet
            df["Típus"] = "Meccs" if "meccs" in sheet.lower() else "Edzés"
            dfs.append(df)
    data = pd.concat(dfs, ignore_index=True)

    numeric_columns = data.select_dtypes(include=np.number).columns.tolist()
    all_players = sorted(data["Játékos neve"].dropna().unique())
    all_weeks = sorted(data["Hét"].unique())
    metrics = [col for col in numeric_columns if col in BENCHMARK_ARANY]

    st.sidebar.header("🎛 Szűrés")
    selected_players = st.sidebar.multiselect("Játékos(ok)", all_players, default=all_players)
    selected_weeks = st.sidebar.multiselect("Hét(ek)", all_weeks, default=all_weeks)
    selected_metrics = st.sidebar.multiselect("Mutatók", metrics, default=metrics[:3])
    tipus = st.sidebar.radio("Típus", ["Mind", "Edzés", "Meccs"])
    pizza_mode = st.sidebar.radio("🍕 Pizza nézet", ["Összes egyben", "Játékosonként"])

    df = data[data["Hét"].isin(selected_weeks)]
    if tipus != "Mind":
        df = df[df["Típus"] == tipus]
    filtered_df = df[df["Játékos neve"].isin(selected_players)]

    st.subheader("📊 Összehasonlító oszlopdiagram")
    for metric in selected_metrics:
        team_avg = df[metric].mean()
        benchmark = BENCHMARK_ARANY.get(metric, 1.0) * df[df["Típus"] == "Meccs"][metric].mean()
        chart_data = []
        for p in selected_players:
            p_val = df[df["Játékos neve"] == p][metric].mean()
            chart_data.append({"Játékos": p, "Érték": p_val, "Típus": "Játékos"})
        chart_data.append({"Játékos": "Csapatátlag", "Érték": team_avg, "Típus": "Csapatátlag"})
        chart_data.append({"Játékos": "Benchmark", "Érték": benchmark, "Típus": "Benchmark"})
        fig = px.bar(pd.DataFrame(chart_data), x="Játékos", y="Érték", color="Típus", barmode="group",
                     title=f"{metric} – játékos vs csapat vs benchmark")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 Trenddiagram (játékos + csapatátlag + benchmark)")
    for metric in selected_metrics:
        pivot = df[df["Játékos neve"].isin(selected_players)].pivot_table(index="Hét", columns="Játékos neve", values=metric).reset_index()
        fig = px.line(pivot, x="Hét", y=pivot.columns[1:], markers=True, title=f"{metric} – trend")
        team_avg = df.groupby("Hét")[metric].mean().reset_index()
        fig.add_scatter(x=team_avg["Hét"], y=team_avg[metric], mode="lines+markers", name="Csapatátlag")
        bm_series = df[df["Típus"] == "Meccs"].groupby("Hét")[metric].mean() * BENCHMARK_ARANY.get(metric, 1.0)
        fig.add_scatter(x=bm_series.index, y=bm_series.values, mode="lines", name="Benchmark", line=dict(dash="dot"))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("🍕 Pizzadiagram(ok)")
    max_val = filtered_df[selected_metrics].max().max()
    if pizza_mode == "Összes egyben":
        fig = px.line_polar(r=[], theta=[], line_close=True)
        for p in selected_players:
            values = filtered_df[filtered_df["Játékos neve"] == p][selected_metrics].mean()
            fig.add_scatterpolar(r=(values / max_val * 100).values, theta=values.index, fill='toself', name=p)
        team_avg = filtered_df[selected_metrics].mean()
        fig.add_scatterpolar(r=(team_avg / max_val * 100).values, theta=team_avg.index, name="Csapatátlag")
        meccs_df = df[df["Típus"] == "Meccs"]
        benchmark_r = [(BENCHMARK_ARANY.get(m, 1.0) * meccs_df[m].mean()) / max_val * 100 for m in selected_metrics]
        fig.add_scatterpolar(r=benchmark_r, theta=selected_metrics, name="Benchmark", line=dict(dash="dot"))
        fig.update_layout(title="Pizza – összes játékos")
        st.plotly_chart(fig, use_container_width=True)
    else:
        for p in selected_players:
            fig = px.line_polar(r=[], theta=[], line_close=True)
            values = filtered_df[filtered_df["Játékos neve"] == p][selected_metrics].mean()
            fig.add_scatterpolar(r=(values / max_val * 100).values, theta=values.index, fill='toself', name=p)
            fig.update_layout(title=f"{p} – pizzadiagram")
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Benchmark táblázat")
    benchmark_table = []
    for metric in selected_metrics:
        meccs_avg = df[df["Típus"] == "Meccs"][metric].mean()
        benchmark_val = BENCHMARK_ARANY.get(metric, 1.0) * meccs_avg
        benchmark_table.append({
            "Mutató": metric,
            "Meccsátlag": round(meccs_avg, 2),
            "Benchmark szorzó": BENCHMARK_ARANY.get(metric, 1.0),
            "Benchmark érték": round(benchmark_val, 2)
        })
    st.dataframe(pd.DataFrame(benchmark_table))
else:
    st.info("📂 Tölts fel legalább egy heti Excel-fájlt több munkalappal (edzések + meccs).")
