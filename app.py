import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Error Analytics Dashboard", layout="wide")
st.title(" Error Analytics Dashboard")

# Google Sheet CSV Export URL (gid=0 explicitly points to the main sheet)
url = "https://docs.google.com/spreadsheets/d/1IihQE0Myys72Ezxhk3OA_kdlmfsjZ2ijIhqTAhYNRYA/export?format=csv&gid=0"


@st.cache_data(ttl=60)
def load_data():
  # Header is on Row 3 (0-indexed position is 2)
  df = pd.read_csv(url, header=2)

  # Clean column names by removing whitespace
  df.columns = df.columns.str.strip()
  return df


df = load_data()

# ---------------- FIND DATE COLUMN ---------------- #
date_col = None
for col in df.columns:
  if "date" in str(col).lower():
    date_col = col
    break

if date_col is None:
  st.error("Date column not found.")
  st.write("Columns detected:", df.columns.tolist())
  st.stop()

# ---------------- DATE CONVERSION ---------------- #
df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
df = df.dropna(subset=[date_col])

# ---------------- SIDEBAR FILTERS ---------------- #
st.sidebar.header("Filters")
min_date = df[date_col].min().date()
max_date = df[date_col].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range", value=(min_date, max_date)
)

if len(date_range) == 1:
  start_date = pd.to_datetime(date_range[0])
  end_date = start_date
else:
  start_date = pd.to_datetime(date_range[0])
  end_date = pd.to_datetime(date_range[1])

df_filtered = df[
    (df[date_col] >= start_date) & (df[date_col] <= end_date)
].copy()

if df_filtered.empty:
  st.warning("No Error Found For Selected Date Range")
  st.stop()

# ---------------- MONTHLY CHART ---------------- #
monthly_errors = (
    df_filtered.groupby(pd.Grouper(key=date_col, freq="MS"))
    .size()
    .reset_index(name="Error Count")
)
monthly_errors = monthly_errors.sort_values(date_col)
monthly_errors["Month"] = monthly_errors[date_col].dt.strftime("%b %Y")

st.subheader(" Month-wise Error Count")
fig_month = px.bar(
    monthly_errors,
    x="Month",
    y="Error Count",
    text="Error Count",
    color="Error Count",
    title="Month-wise Error Analysis",
)
fig_month.update_layout(xaxis_title="Month", yaxis_title="Error Count")
st.plotly_chart(fig_month, use_container_width=True)

# ---------------- ERROR BY ---------------- #
if "Error By" in df_filtered.columns:
  st.subheader(" Error By")
  error_by = (
      df_filtered["Error By"].fillna("Unknown").value_counts().reset_index()
  )
  error_by.columns = ["Person", "Error Count"]
  fig1 = px.bar(
      error_by,
      x="Person",
      y="Error Count",
      text="Error Count",
      color="Error Count",
      title="Errors By Person",
  )
  st.plotly_chart(fig1, use_container_width=True)

# ---------------- CONFIRMATION ---------------- #
confirmation_col = next(
    (col for col in df.columns if "confirmation" in col.lower()), None
)
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
      title="Confirmation Received Analysis",
  )
  st.plotly_chart(fig2, use_container_width=True)

# ---------------- CATEGORY ---------------- #
category_col = next(
    (col for col in df.columns if "category" in col.lower()), None
)
if category_col:
  st.subheader(" Category Analysis")
  category = (
      df_filtered[category_col].fillna("Unknown").value_counts().reset_index()
  )
  category.columns = ["Category", "Count"]
  fig3 = px.bar(
      category,
      x="Category",
      y="Count",
      text="Count",
      color="Count",
      title="Category-wise Error Analysis",
  )
  st.plotly_chart(fig3, use_container_width=True)

# ---------------- RAW DATA ---------------- #
st.subheader(" Raw Data")
st.dataframe(df_filtered, use_container_width=True)
