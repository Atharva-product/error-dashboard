import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Error Analytics Dashboard", layout="wide")

st.title("📊 Error Analytics Dashboard")

# Google Sheet CSV URL
url = "https://docs.google.com/spreadsheets/d/1IihQE0Myys72Ezxhk3OA_kdlmfsjZ2ijIhqTAhYNRYA/export?format=csv"

# Load Data
@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(url)

    # Remove extra spaces
    df.columns = df.columns.str.strip()

    return df

df = load_data()

# Detect date column
date_col = None
for col in df.columns:
    if "date" in col.lower():
        date_col = col
        break

# Convert date format
df[date_col] = pd.to_datetime(
    df[date_col],
    dayfirst=True,
    errors='coerce'
)

df = df.dropna(subset=[date_col])

# Sidebar Filters
st.sidebar.header("Filters")

# Date range filter
min_date = df[date_col].min().date()
max_date = df[date_col].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date]
)

# Handle single date selection
if len(date_range) == 1:
    start_date = end_date = pd.to_datetime(date_range[0])

else:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])

# Apply filter
df_filtered = df[
    (df[date_col] >= start_date) &
    (df[date_col] <= end_date)
]

# If no data found
if df_filtered.empty:
    st.warning(" No Error Found For Selected Date Range")
    st.stop()
# =========================
# MONTH-WISE ERROR COUNT
# =========================

# Create Month-Year column
df_filtered["Month"] = df_filtered[date_col].dt.strftime("%b %Y")

# Count errors month-wise
monthly_errors = (
    df_filtered
    .groupby(pd.Grouper(key=date_col, freq='M'))
    .size()
    .reset_index(name='Error Count')
)

# Create proper labels
monthly_errors["Month"] = monthly_errors[date_col].dt.strftime("%b %Y")

# Plot Bar Chart
st.subheader("📊 Month-wise Error Count")

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

st.plotly_chart(fig_month, width='stretch')

# =========================
# ERROR BY
# =========================
st.subheader("📊 Error By")

error_by = df_filtered["Error By"].value_counts().reset_index()
error_by.columns = ["Person", "Error Count"]

fig1 = px.bar(
    error_by,
    x="Person",
    y="Error Count",
    text="Error Count",
    color="Error Count",
    title="Errors By Person"
)

fig1.update_layout(
    xaxis_title="Person",
    yaxis_title="Number of Errors"
)

st.plotly_chart(fig1, width='stretch')


# =========================
# CONFIRMATION RECEIVED
# =========================
st.subheader("📊 Confirmation Received From Person Who Made Error")

confirmation = df_filtered[
    "Confirmation received from person who made error"
].value_counts().reset_index()

confirmation.columns = ["Person", "Count"]

fig2 = px.bar(
    confirmation,
    x="Person",
    y="Count",
    text="Count",
    color="Count",
    title="Confirmation Received Analysis"
)

fig2.update_layout(
    xaxis_title="Person",
    yaxis_title="Count"
)

st.plotly_chart(fig2, width='stretch')


# =========================
# CATEGORY ANALYSIS
# =========================
st.subheader("📊 Category Analysis")

category = df_filtered["Category"].value_counts().reset_index()
category.columns = ["Category", "Count"]

fig3 = px.bar(
    category,
    x="Category",
    y="Count",
    text="Count",
    color="Count",
    title="Category-wise Error Analysis"
)

fig3.update_layout(
    xaxis_title="Category",
    yaxis_title="Number of Errors"
)

st.plotly_chart(fig3, width='stretch')

# =========================
# RAW DATA
# =========================

st.subheader("📋 Raw Data")

st.dataframe(df_filtered, use_container_width=True)
