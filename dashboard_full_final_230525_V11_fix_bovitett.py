
# ⚽ V11_fix_bővített – Összes mutató, heti szűrés, benchmark, trend, pizza, csapatátlag
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Edzésterhelés V11_bővített", layout="wide")
st.title("⚽ Edzésterhelés – V11 FIX (bővített)")

# Alapértelmezett benchmark arány, ha nincs megadva konkrét érték
ALAP_BENCHMARK_ARANY = 1.0
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

uploaded_files = st.file_uploader("📥 Excel fájl(ok) feltöltése", type="xlsx", accept_multiple_files=True)

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

    players = sorted(data["Játékos neve"].dropna().unique())
    weeks = sorted(data["Hét"].unique())
    numeric_cols = data.select_dtypes(include="number").columns
    metrics = sorted([col for col in numeric_cols if col not in ["Évfolyam"]])  # minden számszerű oszlop megjelenik

    st.sidebar.header("🎛 Szűrés")
    selected_players = st.sidebar.multiselect("Játékos(ok)", players, default=players)
    selected_weeks = st.sidebar.multiselect("Hét(ek)", weeks, default=weeks)
    selected_metrics = st.sidebar.multiselect("Mutatók", metrics, default=metrics[:5])
    tipus = st.sidebar.radio("Típus", ["Mindkettő", "Edzés", "Meccs"])

    df = data[data["Hét"].isin(selected_weeks)]
    if tipus != "Mindkettő":
        df = df[df["Típus"] == tipus]

    if not df.empty and selected_metrics:
        st.subheader("📊 Egyéni vs Csapat vs Benchmark")
        for metric in selected_metrics:
            meccs_val = df[df["Típus"] == "Meccs"][metric].mean()
            benchmark_szorzó = BENCHMARK_ARANY.get(metric, ALAP_BENCHMARK_ARANY)
            benchmark = benchmark_szorzó * meccs_val if not np.isnan(meccs_val) else None
            csapat_avg = df[metric].mean()
            chart_data = []
            for player in selected_players:
                val = df[df["Játékos neve"] == player][metric].mean()
                chart_data.append({"Játékos": player, "Érték": val, "Típus": "Játékos"})
            chart_data.append({"Játékos": "Csapatátlag", "Érték": csapat_avg, "Típus": "Csapatátlag"})
            if benchmark is not None:
                chart_data.append({"Játékos": "Benchmark", "Érték": benchmark, "Típus": "Benchmark"})
            df_chart = pd.DataFrame(chart_data)
            fig = px.bar(df_chart, x="Játékos", y="Érték", color="Típus", title=f"{metric} – összehasonlítás")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🍕 Pizza diagram – Edzés & Meccs")
        for tipus_val in ["Edzés", "Meccs"]:
            pizza_df = df[df["Típus"] == tipus_val]
            if not pizza_df.empty:
                max_val = pizza_df[selected_metrics].max().max()
                fig = px.line_polar(r=[], theta=[], line_close=True, title=f"{tipus_val} – Pizza")
                for player in selected_players:
                    átlag = pizza_df[pizza_df["Játékos neve"] == player][selected_metrics].mean()
                    fig.add_scatterpolar(r=(átlag / max_val * 100).values, theta=átlag.index, fill='toself', name=player)
                csapat_átlag = pizza_df[selected_metrics].mean()
                fig.add_scatterpolar(r=(csapat_átlag / max_val * 100).values, theta=csapat_átlag.index, fill='toself', name="Csapatátlag")
                meccs_df = df[df["Típus"] == "Meccs"]
                ref = [(BENCHMARK_ARANY.get(m, ALAP_BENCHMARK_ARANY) * meccs_df[m].mean()) / max_val * 100 if not np.isnan(meccs_df[m].mean()) else 0 for m in selected_metrics]
                fig.add_scatterpolar(r=ref, theta=selected_metrics, name="Benchmark", line=dict(dash="dot"))
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("📈 Trenddiagram – Hétre bontva")
        for metric in selected_metrics:
            trend_df = df[df["Játékos neve"].isin(selected_players)]
            if not trend_df.empty:
                pivot = trend_df.pivot_table(index="Hét", columns="Játékos neve", values=metric, aggfunc="mean").reset_index()
                fig = px.line(pivot, x="Hét", y=pivot.columns[1:], title=f"{metric} – Játékos trend")
                cs_avg = df.groupby("Hét")[metric].mean().reset_index()
                fig.add_scatter(x=cs_avg["Hét"], y=cs_avg[metric], mode="lines+markers", name="Csapatátlag")
                meccs_df = df[df["Típus"] == "Meccs"].groupby("Hét")[metric].mean()
                benchmark_vals = [(BENCHMARK_ARANY.get(metric, ALAP_BENCHMARK_ARANY) * v) if not np.isnan(v) else None for v in meccs_df]
                fig.add_scatter(x=meccs_df.index, y=benchmark_vals, mode="lines", name="Benchmark", line=dict(dash="dot"))
                st.plotly_chart(fig, use_container_width=True)

else:
    st.info("📥 Tölts fel legalább egy heti Excel-fájlt a kezdéshez.")
