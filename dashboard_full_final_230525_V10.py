
# ⚽ V10 – Edzésterhelés Dashboard (végleges példa)
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Edzésterhelés V10", layout="wide")
st.title("⚽ Edzésterhelés Dashboard – V10 (benchmark, csapatátlag, pizzák)")

uploaded_files = st.file_uploader("📥 Excel(ek) feltöltése", type="xlsx", accept_multiple_files=True)
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

    players = data["Játékos neve"].dropna().unique().tolist()
    weeks = data["Hét"].unique().tolist()
    metrics = [c for c in data.select_dtypes(include="number").columns if c not in ["Kor", "Évfolyam"]]

    st.sidebar.header("🎛️ Szűrők")
    selected_players = st.sidebar.multiselect("Játékos(ok)", players, default=players)
    selected_weeks = st.sidebar.multiselect("Hét(ek)", weeks, default=weeks)
    tipus = st.sidebar.radio("Típus", ["Mindkettő", "Edzés", "Meccs"])
    selected_metrics = st.sidebar.multiselect("Mutatók", metrics, default=metrics[:5])

    df_filtered = data[data["Hét"].isin(selected_weeks)]
    if tipus != "Mindkettő":
        df_filtered = df_filtered[df_filtered["Típus"] == tipus]

    if not df_filtered.empty and selected_metrics:
        st.subheader("📊 Csapat összehasonlítás – teljes csapatátlag vs kiválasztott játékos(ok)")
        csapat_atlag = df_filtered.groupby("Hét")[selected_metrics].mean().mean()
        for player in selected_players:
            p_df = df_filtered[df_filtered["Játékos neve"] == player]
            if not p_df.empty:
                egyeni = p_df[selected_metrics].mean()
                összehasonlítás = pd.DataFrame({
                    "Mutató": selected_metrics,
                    player: egyeni.values,
                    "Csapatátlag": csapat_atlag.values,
                    "Benchmark": [100 for _ in selected_metrics]
                })
                fig = px.bar(összehasonlítás, x="Mutató", y=[player, "Csapatátlag", "Benchmark"], barmode="group", title=f"{player} vs Csapat + Benchmark")
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("🍕 Pizza – Edzés és Meccs összehasonlítás (normalizált)")
        for tipus_val in ["Edzés", "Meccs"]:
            pizza_df = df_filtered[df_filtered["Típus"] == tipus_val]
            norm_max = pizza_df[selected_metrics].max().max()
            fig = px.line_polar(r=[], theta=[], line_close=True)
            for player in selected_players:
                avg = pizza_df[pizza_df["Játékos neve"] == player][selected_metrics].mean()
                fig.add_scatterpolar(r=avg.values / norm_max * 100, theta=avg.index, fill='toself', name=player)
            team_avg = pizza_df[selected_metrics].mean()
            fig.add_scatterpolar(r=team_avg.values / norm_max * 100, theta=team_avg.index, fill='toself', name="Csapatátlag")
            benchmark = np.ones(len(selected_metrics)) * 80
            fig.add_scatterpolar(r=benchmark, theta=selected_metrics, name="Benchmark", line=dict(dash="dot"))
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("📈 Trend – Játékosonként")
        for m in selected_metrics:
            trend_df = df_filtered[df_filtered["Játékos neve"].isin(selected_players)]
            pivot = trend_df.pivot_table(index="Hét", columns="Játékos neve", values=m, aggfunc="mean").reset_index()
            fig = px.line(pivot, x="Hét", y=pivot.columns[1:], title=f"Trend: {m}")
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("📥 Tölts fel legalább egy heti Excel-fájlt a kezdéshez.")
