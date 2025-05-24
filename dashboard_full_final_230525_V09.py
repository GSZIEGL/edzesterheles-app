
# ⚽ V09 – Teljes edzésterhelés dashboard
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Edzésterhelés V09", layout="wide")
st.title("⚽ Edzésterhelés Dashboard – V09 (végleges minta)")

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
    selected_players = st.sidebar.multiselect("Játékos(ok)", players, default=players[:1])
    selected_weeks = st.sidebar.multiselect("Hét(ek)", weeks, default=weeks)
    tipus = st.sidebar.radio("Típus", ["Mindkettő", "Edzés", "Meccs"])

    if tipus == "Mindkettő":
        df_filtered = data[data["Hét"].isin(selected_weeks)]
    else:
        df_filtered = data[(data["Típus"] == tipus) & (data["Hét"].isin(selected_weeks))]

    selected_metrics = st.sidebar.multiselect("Mutatók", metrics)

    if not df_filtered.empty and selected_metrics:
        st.subheader("📊 Csapat – Normalizált Összehasonlítás")
        csapat_df = df_filtered.copy()
        for m in selected_metrics:
            max_val = df_filtered[m].max()
            csapat_df[m] = df_filtered[m] / max_val * 100 if max_val else 0
        fig = px.bar(csapat_df, x="Játékos neve", y=selected_metrics, barmode="group")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📈 Egyéni – Trenddiagram")
        for m in selected_metrics:
            pivot = df_filtered.pivot_table(index="Hét", columns="Játékos neve", values=m, aggfunc="mean").reset_index()
            fig = px.line(pivot, x="Hét", y=pivot.columns[1:], title=f"Trend – {m}", markers=True)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🍕 Pizza – Játékosok összehasonlítása (edzés)")
        pizza_df = df_filtered[df_filtered["Típus"] == "Edzés"]
        for player in selected_players:
            avg = pizza_df[pizza_df["Játékos neve"] == player][selected_metrics].mean()
            chart = pd.DataFrame({"Mutató": avg.index, "Érték": avg.values})
            fig = px.line_polar(chart, r="Érték", theta="Mutató", line_close=True, title=f"{player} – Edzés")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🍕 Pizza – Játékosok összehasonlítása (meccs)")
        pizza_df = df_filtered[df_filtered["Típus"] == "Meccs"]
        for player in selected_players:
            avg = pizza_df[pizza_df["Játékos neve"] == player][selected_metrics].mean()
            chart = pd.DataFrame({"Mutató": avg.index, "Érték": avg.values})
            fig = px.line_polar(chart, r="Érték", theta="Mutató", line_close=True, title=f"{player} – Meccs")
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("📥 Kérlek, tölts fel legalább egy heti Excel-fájlt.")
