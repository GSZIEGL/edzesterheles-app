
# Streamlit edzésterhelés dashboard – újratervezett, nulláról épített változat
# Minden fontos mutatóval, szűrőkkel és benchmarkkal, több heti adat kezelésével

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Edzésterhelés App", layout="wide")

st.title("⚽ Interaktív Edzésterhelés Dashboard")

uploaded_file = st.file_uploader("📤 Tölts fel egy Excel fájlt (több heti edzéssel és meccsel)", type="xlsx")

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    all_dfs = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["Hét"] = sheet
        all_dfs.append(df)
    return pd.concat(all_dfs, ignore_index=True)

def radar_chart(df, columns, ref_dict, title):
    cols = [col for col in columns if col in df.columns]
    if not cols:
        return None
    avg_vals = df[cols].mean()
    norm_vals = [avg_vals[c]/ref_dict[c]*100 if ref_dict.get(c) else 0 for c in cols]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=norm_vals, theta=cols, fill='toself', name='Játékos'))
    fig.add_trace(go.Scatterpolar(r=[100]*len(cols), theta=cols, fill='toself', name='Benchmark'))
    fig.update_layout(title=title, polar=dict(radialaxis=dict(visible=True, range=[0, max(120, max(norm_vals, default=0))])))
    return fig

if uploaded_file:
    df = load_data(uploaded_file)
    df = df[df["Játékos neve"].notna()]
    st.sidebar.header("🎯 Szűrés")

    players = sorted(df["Játékos neve"].dropna().unique().tolist())
    types = sorted(df["Típus"].dropna().unique().tolist())
    weeks = sorted(df["Hét"].dropna().unique().tolist())
    all_metrics = [c for c in df.columns if df[c].dtype in ['int64', 'float64'] and c not in ['Évfolyam', 'Kor']]

    selected_player = st.sidebar.selectbox("Játékos", players)
    selected_type = st.sidebar.selectbox("Típus (edzés/meccs)", ["Összes"] + types)
    selected_weeks = st.sidebar.multiselect("Hét(ek)", weeks, default=weeks)
    selected_metrics = st.sidebar.multiselect("Mutatók", all_metrics, default=all_metrics)

    filtered = df[df["Játékos neve"] == selected_player]
    if selected_type != "Összes":
        filtered = filtered[filtered["Típus"] == selected_type]
    filtered = filtered[filtered["Hét"].isin(selected_weeks)]

    team_filtered = df[df["Hét"].isin(selected_weeks)]
    if selected_type != "Összes":
        team_filtered = team_filtered[team_filtered["Típus"] == selected_type]

    st.header(f"📊 {selected_player} teljesítménye ({', '.join(selected_weeks)})")

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

    col1, col2 = st.columns(2)
    with col1:
        fig1 = radar_chart(filtered, ["Teljes táv [m]", "Táv/perc [m/perc]", "Max sebesség [km/h]", "Sprintek száma"], ref_values, "🕸️ Fizikai mutatók")
        if fig1: st.plotly_chart(fig1, use_container_width=True)
    with col2:
        fig2 = radar_chart(filtered, ["Izomterhelés", "HRV (RMSSD)", "Átlagos pulzus [bpm]"], ref_values, "🕸️ Terhelés mutatók")
        if fig2: st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📈 Trendmutatók (játékos, heti bontásban)")
    if "Hét" in filtered.columns:
        trend_df = filtered.groupby("Hét")[selected_metrics].mean().reset_index()
        fig = px.line(trend_df, x="Hét", y=selected_metrics, markers=True)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📊 Csapatátlag vs játékos (választott mutatók)")
    compare_df = pd.DataFrame({
        "Mutató": selected_metrics,
        "Játékos": [filtered[m].mean() if m in filtered.columns else None for m in selected_metrics],
        "Csapat": [team_filtered[m].mean() if m in team_filtered.columns else None for m in selected_metrics],
        "Benchmark": [ref_values.get(m, None) for m in selected_metrics]
    })
    fig_comp = px.bar(compare_df, x="Mutató", y=["Játékos", "Csapat", "Benchmark"], barmode="group")
    st.plotly_chart(fig_comp, use_container_width=True)

    st.subheader("📋 Adattábla")
    st.dataframe(filtered[selected_metrics + ["Hét", "Típus"]])
else:
    st.info("Kérlek, tölts fel egy Excel fájlt a használathoz.")
