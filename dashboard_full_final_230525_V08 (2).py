
# ⚽ V08 – Edzésterhelés Streamlit app (végleges minta, működő szerkezettel)
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Edzésterhelés V08", layout="wide")
st.title("⚽ Edzésterhelés Dashboard – V08 (minta)")

uploaded_files = st.file_uploader("📥 Excel fájl(ok) feltöltése", type="xlsx", accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for file in uploaded_files:
        xls = pd.ExcelFile(file)
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df["Hét"] = sheet
            dfs.append(df)
    data = pd.concat(dfs, ignore_index=True)

    st.success(f"{len(data)} sor betöltve {len(uploaded_files)} fájlból.")
    players = data["Játékos neve"].dropna().unique().tolist()
    weeks = data["Hét"].unique().tolist()
    metrics = [c for c in data.select_dtypes(include="number").columns if c not in ["Kor", "Évfolyam"]]

    selected_players = st.sidebar.multiselect("🎯 Játékos(ok)", players, default=players[:1])
    selected_weeks = st.sidebar.multiselect("📅 Hét(ek)", weeks, default=weeks)
    selected_metrics = st.sidebar.multiselect("📈 Mutatók", metrics)

    df_filtered = data[
        (data["Játékos neve"].isin(selected_players)) & (data["Hét"].isin(selected_weeks))
    ]

    if not df_filtered.empty and selected_metrics:
        st.subheader("📊 Összehasonlító (normalizált)")
        norm_df = df_filtered.copy()
        for m in selected_metrics:
            max_val = df_filtered[m].max()
            norm_df[m] = df_filtered[m] / max_val * 100 if max_val else 0
        fig = px.bar(norm_df, x="Játékos neve", y=selected_metrics, barmode="group")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🍕 Pizzadiagram (játékosonként)")
        for player in selected_players:
            p_df = df_filtered[df_filtered["Játékos neve"] == player]
            if not p_df.empty:
                avg = p_df[selected_metrics].mean()
                pizza = pd.DataFrame({
                    "Mutató": avg.index,
                    "Érték": avg.values
                })
                fig = px.line_polar(pizza, r="Érték", theta="Mutató", line_close=True, title=player)
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("📈 Trend mutatónként (hetek szerint)")
        for m in selected_metrics:
            pivot = df_filtered.pivot_table(index="Hét", columns="Játékos neve", values=m, aggfunc="mean").reset_index()
            fig = px.line(pivot, x="Hét", y=pivot.columns[1:], title=f"Trend – {m}", markers=True)
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Tölts fel legalább egy heti Excel fájlt a kezdéshez.")
