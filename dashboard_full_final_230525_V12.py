
# ⚽ V12 – Végleges verzió: benchmark, heti szűrés, pizza, trend, választható nézetek
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Edzésterhelés – V12", layout="wide")
st.title("⚽ Edzésterhelés Dashboard – V12 végleges")

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
DEFAULT_BENCHMARK = 1.0

uploaded_files = st.file_uploader("📁 Excel fájl(ok) feltöltése (több hét)", type="xlsx", accept_multiple_files=True)

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

    all_metrics = data.select_dtypes(include=np.number).columns.tolist()
    metrics = [m for m in all_metrics if m in BENCHMARK_ARANY]

    st.sidebar.header("🎛 Szűrők")
    all_players = sorted(data["Játékos neve"].dropna().unique())
    all_weeks = sorted(data["Hét"].unique())

    selected_players = st.sidebar.multiselect("Játékos(ok)", all_players, default=all_players)
    selected_weeks = st.sidebar.multiselect("Hét(ek)", all_weeks, default=all_weeks)
    selected_metrics = st.sidebar.multiselect("Mutatók", metrics, default=metrics[:5])
    selected_típus = st.sidebar.radio("Típus", ["Mindkettő", "Edzés", "Meccs"])
    pizza_mode = st.sidebar.radio("🍕 Pizza nézet", ["Összes egyben", "Játékosonként külön"])

    df = data[data["Hét"].isin(selected_weeks)]
    if selected_típus != "Mindkettő":
        df = df[df["Típus"] == selected_típus]

    filtered_df = df[df["Játékos neve"].isin(selected_players)]

    if not filtered_df.empty and selected_metrics:
        st.subheader("📊 Összehasonlító oszlopdiagram (Játékos vs Csapat vs Benchmark)")
        for metric in selected_metrics:
            meccs_avg = df[df["Típus"] == "Meccs"][metric].mean()
            benchmark_value = BENCHMARK_ARANY.get(metric, DEFAULT_BENCHMARK) * meccs_avg
            team_avg = df[metric].mean()

            chart_data = []
            for player in selected_players:
                player_avg = df[df["Játékos neve"] == player][metric].mean()
                chart_data.append({"Név": player, "Érték": player_avg, "Típus": "Játékos"})
            chart_data.append({"Név": "Csapatátlag", "Érték": team_avg, "Típus": "Csapatátlag"})
            chart_data.append({"Név": "Benchmark", "Érték": benchmark_value, "Típus": "Benchmark"})

            fig = px.bar(pd.DataFrame(chart_data), x="Név", y="Érték", color="Típus", barmode="group",
                         title=f"{metric} – játékos vs csapat vs benchmark")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("📈 Trenddiagram – Játékos(ok), Csapatátlag, Benchmark")
        for metric in selected_metrics:
            pivot = df[df["Játékos neve"].isin(selected_players)].pivot_table(index="Hét", columns="Játékos neve", values=metric, aggfunc="mean").reset_index()
            fig = px.line(pivot, x="Hét", y=pivot.columns[1:], markers=True, title=f"{metric} – trend játékosonként")

            team_avg = df.groupby("Hét")[metric].mean().reset_index()
            fig.add_scatter(x=team_avg["Hét"], y=team_avg[metric], mode="lines+markers", name="Csapatátlag")

            meccs_benchmark = df[df["Típus"] == "Meccs"].groupby("Hét")[metric].mean() * BENCHMARK_ARANY.get(metric, DEFAULT_BENCHMARK)
            fig.add_scatter(x=meccs_benchmark.index, y=meccs_benchmark.values, mode="lines", name="Benchmark", line=dict(dash="dot"))

            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🍕 Pizzadiagram(ok) – Játékos(ok), Csapatátlag, Benchmark")

        def get_pizza_data(df_input):
            max_val = df_input[selected_metrics].max().max()
            scaled = df_input[selected_metrics].mean() / max_val * 100 if max_val > 0 else df_input[selected_metrics].mean()
            return scaled

        if pizza_mode == "Összes egyben":
            fig = px.line_polar(r=[], theta=[], line_close=True)
            max_val = filtered_df[selected_metrics].max().max()
            for player in selected_players:
                p_avg = filtered_df[filtered_df["Játékos neve"] == player][selected_metrics].mean()
                fig.add_scatterpolar(r=(p_avg / max_val * 100).values, theta=p_avg.index, fill='toself', name=player)
            team_avg = filtered_df[selected_metrics].mean()
            fig.add_scatterpolar(r=(team_avg / max_val * 100).values, theta=team_avg.index, fill='toself', name="Csapatátlag")
            meccs_df = df[df["Típus"] == "Meccs"]
            ref = [(BENCHMARK_ARANY.get(m, DEFAULT_BENCHMARK) * meccs_df[m].mean()) / max_val * 100 if not np.isnan(meccs_df[m].mean()) else 0 for m in selected_metrics]
            fig.add_scatterpolar(r=ref, theta=selected_metrics, name="Benchmark", line=dict(dash="dot"))
            fig.update_layout(title="🍕 Összesített pizzadiagram")
            st.plotly_chart(fig, use_container_width=True)
        else:
            for player in selected_players:
                fig = px.line_polar(r=[], theta=[], line_close=True)
                p_avg = filtered_df[filtered_df["Játékos neve"] == player][selected_metrics].mean()
                max_val = filtered_df[selected_metrics].max().max()
                fig.add_scatterpolar(r=(p_avg / max_val * 100).values, theta=p_avg.index, fill='toself', name=player)
                fig.update_layout(title=f"🍕 {player} – pizzadiagram")
                st.plotly_chart(fig, use_container_width=True)
else:
    st.info("📥 Tölts fel legalább egy heti Excel-fájlt.")
