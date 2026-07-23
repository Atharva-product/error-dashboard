import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Error Analytics Dashboard", layout="wide")

st.title("📊 Error Analytics Dashboard")

# Google Sheet CSV URL
url = "https://docs.google.com/spreadsheets/d/1IihQE0Myys72Ezxhk3OA_kdlmfsjZ2ijIhqTAhYNRYA/export?format=csv"


@st.cache_data(ttl=60)
def load_data():
    # Skip first two rows because actual headers start from row 3
    df = pd.read_csv(url, header=2)

    # Clean column names
    df.columns = (
        df.columns
        .str.strip()
        .str.replace("*", "", regex=False)
    )

    return df


df = load_data()

# ---------------- FIND DATE COLUMN ---------------- #

date_col = None

for col in df.columns:
    if "date" in col.lower():
        date_col = col
        break

if date_col is None:
    st.error("Date column not found.")
    st.write("Columns detected:", df.columns.tolist())
    st.stop()

# ---------------- DATE CONVERSION ---------------- #

df[date_col] = pd.to_datetime(
    df[date_col],
    dayfirst=True,
    errors="coerce"
)

df = df.dropna(subset=[date_col])

# ---------------- SIDEBAR ---------------- #

st.sidebar.header("Filters")

min_date = df[date_col].min().date()
max_date = df[date_col].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date)
)

if len(date_range) == 1:
    start_date = pd.to_datetime(date_range[0])
    end_date = start_date
else:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])

df_filtered = df[
    (df[date_col] >= start_date) &
    (df[date_col] <= end_date)
]

if df_filtered.empty:
    st.warning("No Error Found For Selected Date Range")
    st.stop()

# ---------------- MONTHLY CHART ---------------- #

monthly_errors = (
    df_filtered
    .groupby(pd.Grouper(key=date_col, freq="MS"))
    .size()
    .reset_index(name="Error Count")
)

monthly_errors = monthly_errors.sort_values(date_col)

monthly_errors["Month"] = monthly_errors[date_col].dt.strftime("%b %Y")

st.subheader("📅 Month-wise Error Count")

fig_month = px.bar(
    monthly_errors,
    x="Month",
    y="Error Count",
    text="Error Count",
    color="Error Count",
    title="Month-wise Error Analysis"
)

fig_month.update_layout(
    xaxis_title="Month",
    yaxis_title="Error Count"
)

st.plotly_chart(fig_month, width="stretch")

# ---------------- ERROR BY ---------------- #

st.subheader("👤 Error By")

error_by = (
    df_filtered["Error By"]
    .fillna("Unknown")
    .value_counts()
    .reset_index()
)

error_by.columns = ["Person", "Error Count"]

fig1 = px.bar(
    error_by,
    x="Person",
    y="Error Count",
    text="Error Count",
    color="Error Count",
    title="Errors By Person"
)

st.plotly_chart(fig1, width="stretch")

# ---------------- CONFIRMATION ---------------- #

confirmation_col = None

for col in df.columns:
    if "confirmation" in col.lower():
        confirmation_col = col
        break

if confirmation_col:

    st.subheader(" Confirmation Received From Person Who Made Error")

    confirmation = (
        df_filtered[confirmation_col]
        .fillna("Unknown")
        .value_counts()
        .reset_index()
    )

    confirmation.columns = ["Person", "Count"]

    fig2 = px.bar(
        confirmation,
        x="Person",
        y="Count",
        text="Count",
        color="Count",
        title="Confirmation Received Analysis"
    )

    st.plotly_chart(fig2, width="stretch")

# ---------------- CATEGORY ---------------- #

category_col = None

for col in df.columns:
    if "category" in col.lower():
        category_col = col
        break

if category_col:

    st.subheader(" Category Analysis")

    category = (
        df_filtered[category_col]
        .fillna("Unknown")
        .value_counts()
        .reset_index()
    )

    category.columns = ["Category", "Count"]

    fig3 = px.bar(
        category,
        x="Category",
        y="Count",
        text="Count",
        color="Count",
        title="Category-wise Error Analysis"
    )

    st.plotly_chart(fig3, width="stretch")

# ---------------- RAW DATA ---------------- #

st.subheader("📋 Raw Data")

st.dataframe(df_filtered, width="stretch")
