
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from io import StringIO

st.set_page_config(page_title="Edzésterhelés Dashboard", layout="wide")
st.title("🏆 Heti edzésterhelés elemző alkalmazás")

# --- Funkciók ---
def load_all_sheets(file):
    excel = pd.ExcelFile(file)
    sheets = excel.sheet_names
    dfs = []
    for sheet in sheets:
        df = pd.read_excel(excel, sheet_name=sheet)
        df['Forrás'] = sheet
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

def preprocess(df):
    df = df.copy()
    df = df[df["Játékos neve"].notna()]
    df["Kezdési idő"] = pd.to_datetime(df["Kezdési idő"], errors="coerce")
    df["Átlagos pulzus [bpm]"] = pd.to_numeric(df["Átlagos pulzus [bpm]"], errors="coerce")
    df["Izomterhelés"] = pd.to_numeric(df["Izomterhelés"], errors="coerce")
    df["HRV (RMSSD)"] = pd.to_numeric(df["HRV (RMSSD)"], errors="coerce")
    df["Időtartam"] = pd.to_timedelta(df["Időtartam"], errors="coerce")
    df["Időtartam perc"] = df["Időtartam"].dt.total_seconds() / 60
    df["Edzés/meccs"] = df["Forrás"].apply(lambda x: "Meccs" if "meccs" in x.lower() else "Edzés")
    return df

def calculate_summary(df):
    agg = df.groupby("Játékos neve").agg({
        "Átlagos pulzus [bpm]": "mean",
        "Izomterhelés": "sum",
        "HRV (RMSSD)": "mean",
        "Időtartam perc": "sum"
    }).rename(columns={
        "Átlagos pulzus [bpm]": "Átlagos pulzus",
        "Izomterhelés": "Összes izomterhelés",
        "HRV (RMSSD)": "Átlagos HRV",
        "Időtartam perc": "Össz idő (perc)"
    })
    return agg.reset_index()

# --- Fő rész ---
uploaded_file = st.file_uploader("Töltsd fel az edzés/meccs adatokat tartalmazó Excel fájlt (több munkalap megengedett)", type="xlsx")

if uploaded_file:
    df_raw = load_all_sheets(uploaded_file)
    df = preprocess(df_raw)

    st.sidebar.header("🔍 Szűrés")
    selected_players = st.sidebar.multiselect("Játékos kiválasztása", df["Játékos neve"].unique().tolist(), default=df["Játékos neve"].unique().tolist())
    df = df[df["Játékos neve"].isin(selected_players)]

    st.subheader("📊 Játékosok összesített statisztikái")
    summary_df = calculate_summary(df)
    st.dataframe(summary_df)

    st.subheader("🏋️ Izomterhelés - Top 10")
    top10 = summary_df.sort_values("Összes izomterhelés", ascending=False).head(10)
    fig1 = px.bar(top10, x="Játékos neve", y="Összes izomterhelés", title="Top 10 játékos izomterhelés szerint")
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("🌐 HRV trend időben")
    fig2 = px.line(df, x="Kezdési idő", y="HRV (RMSSD)", color="Játékos neve", markers=True)
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Kérlek tölts fel egy Excel fájlt, amely tartalmazza az edzés/meccs adatokat.")
