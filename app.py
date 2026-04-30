import pandas as pd
import streamlit as st

st.set_page_config(page_title="Analytical Dashboard", layout="wide")

st.title("📊Error Analysis Dashboard")

url = "https://docs.google.com/spreadsheets/d/1IihQE0Myys72Ezxhk3OA_kdlmfsjZ2ijIhqTAhYNRYA/export?format=csv"

@st.cache_data(ttl=10)
def load_data():
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

df = load_data()

date_col = None
for col in df.columns:
    if "date" in col.lower() or "time" in col.lower():
        date_col = col
        break

if date_col is None:
    st.error("No Date column found")
    st.stop()

df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
df = df.dropna(subset=[date_col])

st.sidebar.header("Filters")

min_date = df[date_col].min()
max_date = df[date_col].max()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

df_filtered = df[
    (df[date_col] >= pd.to_datetime(date_range[0])) &
    (df[date_col] <= pd.to_datetime(date_range[1]))
]

daily_summary = df_filtered.groupby(df_filtered[date_col].dt.date).size()

daily_summary = daily_summary.reset_index()
daily_summary.columns = ['Date', 'Error Count']

daily_summary = daily_summary.sort_values('Date')

st.subheader("📈 Errors Over Time")

if not daily_summary.empty:
    st.line_chart(daily_summary.set_index('Date'))
else:
    st.warning("No data available for selected range")

st.subheader("📋 Raw Data")
st.dataframe(df_filtered, use_container_width=True)
