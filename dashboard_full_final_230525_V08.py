
# ⚽ V08 – Edzésterhelés Dashboard (Streamlit app – bemutató tömör verzió)

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Edzésterhelés V08", layout="wide")
st.title("⚽ Edzésterhelés Elemző – V08")

uploaded_files = st.file_uploader("📥 Excel(ek) feltöltése", type="xlsx", accept_multiple_files=True)
if uploaded_files:
    df_list = []
    for file in uploaded_files:
        xls = pd.ExcelFile(file)
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df["Hét"] = sheet
            df_list.append(df)
    df_all = pd.concat(df_list, ignore_index=True)
    st.success(f"{len(df_all)} sor betöltve {len(uploaded_files)} fájlból.")

    players = df_all["Játékos neve"].dropna().unique().tolist()
    weeks = df_all["Hét"].dropna().unique().tolist()
    metrics = [c for c in df_all.select_dtypes(include="number").columns if c not in ["Kor", "Évfolyam"]]

    selected_players = st.sidebar.multiselect("Játékos(ok)", players, default=players[:1])
    selected_weeks = st.sidebar.multiselect("Hét(ek)", weeks, default=weeks)
    selected_metrics = st.sidebar.multiselect("Mutatók", metrics)

    df_filtered = df_all[
        (df_all["Játékos neve"].isin(selected_players)) & (df_all["Hét"].isin(selected_weeks))
    ]

    if not df_filtered.empty and selected_metrics:
        st.subheader("📊 Normalizált Összehasonlítás")
        norm_df = df_filtered.copy()
        for m in selected_metrics:
            max_val = df_filtered[m].max()
            norm_df[m] = df_filtered[m] / max_val * 100 if max_val else 0
        fig = px.bar(norm_df, x="Játékos neve", y=selected_metrics, barmode="group")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📈 Mutatónkénti trend (hetek szerint)")
        for m in selected_metrics:
            pivot = df_filtered.pivot_table(index="Hét", columns="Játékos neve", values=m, aggfunc="mean").reset_index()
            fig = px.line(pivot, x="Hét", y=pivot.columns[1:], title=m, markers=True)
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Tölts fel legalább egy fájlt az elemzéshez.")
