
# ⚽ V11_fix – Edzésterhelés Dashboard (benchmark, hét szűrés, trend, javított pizzák)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Edzésterhelés V11_fix", layout="wide")
st.title("⚽ Edzésterhelés Dashboard – V11 FIX")

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
    metrics = [col for col in numeric_cols if col in BENCHMARK_ARANY]

    st.sidebar.header("🎛 Szűrés")
    selected_players = st.sidebar.multiselect("Játékos(ok)", players, default=players)
    selected_weeks = st.sidebar.multiselect("Hét(ek)", weeks, default=weeks)
    selected_metrics = st.sidebar.multiselect("Mutatók", metrics, default=metrics[:6])
    tipus = st.sidebar.radio("Típus", ["Mindkettő", "Edzés", "Meccs"])

    df = data[data["Hét"].isin(selected_weeks)]
    if tipus != "Mindkettő":
        df = df[df["Típus"] == tipus]

    if not df.empty and selected_metrics:
        st.subheader("📊 Egyéni vs Csapat vs Benchmark (oszlop + vonal)")
        for metric in selected_metrics:
            csapat_meccs = df[df["Típus"] == "Meccs"][metric].mean()
            benchmark_val = BENCHMARK_ARANY.get(metric, 1.0) * csapat_meccs if not np.isnan(csapat_meccs) else None
            csapat_avg = df[metric].mean()
            chart_data = []
            for player in selected_players:
                val = df[df["Játékos neve"] == player][metric].mean()
                chart_data.append({
                    "Típus": "Játékos",
                    "Játékos": player,
                    "Mutató": metric,
                    "Érték": val
                })
            chart_data.append({"Típus": "Csapatátlag", "Játékos": "Csapatátlag", "Mutató": metric, "Érték": csapat_avg})
            if benchmark_val is not None:
                chart_data.append({"Típus": "Benchmark", "Játékos": "Benchmark", "Mutató": metric, "Érték": benchmark_val})
            df_plot = pd.DataFrame(chart_data)
            fig = px.bar(df_plot, x="Játékos", y="Érték", color="Típus", title=f"{metric} összehasonlítása")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🍕 Pizzadiagram – Edzés és Meccs")
        for tipus_val in ["Edzés", "Meccs"]:
            pizza_df = df[df["Típus"] == tipus_val]
            if not pizza_df.empty:
                max_val = pizza_df[selected_metrics].max().max()
                fig = px.line_polar(r=[], theta=[], line_close=True, title=f"{tipus_val} Pizza")
                for player in selected_players:
                    avg = pizza_df[pizza_df["Játékos neve"] == player][selected_metrics].mean()
                    if not avg.isnull().all():
                        fig.add_scatterpolar(r=avg.values / max_val * 100, theta=avg.index, fill='toself', name=player)
                team_avg = pizza_df[selected_metrics].mean()
                fig.add_scatterpolar(r=team_avg.values / max_val * 100, theta=team_avg.index, fill='toself', name="Csapatátlag")
                meccs_df = df[df["Típus"] == "Meccs"]
                ref = [BENCHMARK_ARANY.get(m, 1.0) * meccs_df[m].mean() / max_val * 100 if not np.isnan(meccs_df[m].mean()) else 0 for m in selected_metrics]
                fig.add_scatterpolar(r=ref, theta=selected_metrics, name="Benchmark", line=dict(dash="dot"))
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("📈 Trend – játékosok, csapatátlag, benchmark")
        for metric in selected_metrics:
            trend_df = df[df["Játékos neve"].isin(selected_players)]
            if not trend_df.empty:
                pivot = trend_df.pivot_table(index="Hét", columns="Játékos neve", values=metric, aggfunc="mean").reset_index()
                fig = px.line(pivot, x="Hét", y=pivot.columns[1:], title=f"{metric} – Trend")
                cs_avg = df.groupby("Hét")[metric].mean().reset_index()
                fig.add_scatter(x=cs_avg["Hét"], y=cs_avg[metric], mode="lines+markers", name="Csapatátlag")
                meccs_df = df[df["Típus"] == "Meccs"].groupby("Hét")[metric].mean()
                bench = [BENCHMARK_ARANY.get(metric, 1.0) * v if not np.isnan(v) else None for v in meccs_df]
                fig.add_scatter(x=meccs_df.index, y=bench, mode="lines", name="Benchmark", line=dict(dash="dot"))
                st.plotly_chart(fig, use_container_width=True)

else:
    st.info("📥 Tölts fel legalább egy heti Excel-fájlt a kezdéshez.")
