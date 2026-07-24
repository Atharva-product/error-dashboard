import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Error Analytics Dashboard", layout="wide")
st.title(" Error Analytics Dashboard")

url = "https://docs.google.com/spreadsheets/d/1IihQE0Myys72Ezxhk3OA_kdlmfsjZ2ijIhqTAhYNRYA/export?format=csv&gid=0"


# Temporarily removed cache decorator to ensure fresh data fetch
def load_data():
  df = pd.read_csv(url, header=2)
  df.columns = df.columns.str.strip()
  return df


df = load_data()

# Find date column
date_col = next(
    (col for col in df.columns if "date" in str(col).lower()), None
)

if date_col is None:
  st.error("Date column not found.")
  st.stop()

# Parse dates flexibly (handles mixed formats & times)
df[date_col] = pd.to_datetime(df[date_col], format="mixed", errors="coerce")
df = df.dropna(subset=[date_col])

# ---------------- SIDEBAR FILTERS ---------------- #
st.sidebar.header("Filters")

# Extract exact min and max dates from the dataset
data_min_date = df[date_col].min().date()
data_max_date = df[date_col].max().date()

# Pass min_value and max_value to restrict selection within dataset limits
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(data_min_date, data_max_date),
    min_value=data_min_date,
    max_value=data_max_date,
)

# Ensure start and end cover full days
if len(date_range) == 2:
  start_date = pd.to_datetime(date_range[0]).replace(
      hour=0, minute=0, second=0
  )
  end_date = pd.to_datetime(date_range[1]).replace(
      hour=23, minute=59, second=59
  )
elif len(date_range) == 1:
  start_date = pd.to_datetime(date_range[0]).replace(
      hour=0, minute=0, second=0
  )
  end_date = pd.to_datetime(date_range[0]).replace(
      hour=23, minute=59, second=59
  )
else:
  start_date = pd.to_datetime(data_min_date).replace(
      hour=0, minute=0, second=0
  )
  end_date = pd.to_datetime(data_max_date).replace(
      hour=23, minute=59, second=59
  )

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

# Keep only months that actually have data
monthly_errors = monthly_errors[monthly_errors["Error Count"] > 0]
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

# Force the X-axis to treat months as categorical labels (prevents Plotly from padding empty future months)
fig_month.update_xaxes(type="category")
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
