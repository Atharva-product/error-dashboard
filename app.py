import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Error Analytics Dashboard", layout="wide")
st.title(" Error Analytics Dashboard")

# Google Sheet CSV Export Link
url = "https://docs.google.com/spreadsheets/d/1IihQE0Myys72Ezxhk3OA_kdlmfsjZ2ijIhqTAhYNRYA/export?format=csv&gid=0"


def load_data():
  # Header starts on Row 3 (index 2)
  df = pd.read_csv(url, header=2)
  df.columns = df.columns.str.strip()
  return df


df = load_data()

# Identify Date column dynamically
date_col = next(
    (col for col in df.columns if "date" in str(col).lower()), None
)

if date_col is None:
  st.error("Date column not found.")
  st.stop()

# ---------------- ROBUST DATE PARSING ---------------- #
# Clean string whitespace first
df[date_col] = df[date_col].astype(str).str.strip()

# Parse mixed date formats (DD-MM-YYYY, YYYY-MM-DD, etc.) without coercing July to NaT
df[date_col] = pd.to_datetime(
    df[date_col], format="mixed", dayfirst=True, errors="coerce"
)
df = df.dropna(subset=[date_col])

# Formatted display date string
df["Formatted Date"] = df[date_col].dt.strftime("%Y-%m-%d")

# ---------------- SIDEBAR FILTERS ---------------- #
st.sidebar.header("Filters")

data_min_date = df[date_col].min().date()
data_max_date = df[date_col].max().date()

# Force key update so Streamlit picks up the new max date automatically
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(data_min_date, data_max_date),
    min_value=data_min_date,
    max_value=data_max_date,
    key="date_range_picker_v3",
)

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
fig_month.update_xaxes(type="category")
fig_month.update_layout(xaxis_title="Month", yaxis_title="Error Count")
st.plotly_chart(fig_month, use_container_width=True)

# Create a Month column for grouping
df_filtered["Month_Year"] = df_filtered[date_col].dt.strftime("%b %Y")

# Sort months chronologically
df_filtered = df_filtered.sort_values(by=date_col)

# ---------------- MONTHLY CONFIRMATION ANALYSIS ---------------- #
confirmation_col = next(
    (col for col in df.columns if "confirmation" in col.lower()), None
)

if confirmation_col:
  st.subheader(" Monthly Confirmation Received Breakdown")

  # Group by Month and Confirmation Status
  monthly_conf = (
      df_filtered.groupby(["Month_Year", confirmation_col], sort=False)
      .size()
      .reset_index(name="Count")
  )

  # Plot Stacked/Grouped Bar Chart
  fig_monthly_conf = px.bar(
      monthly_conf,
      x="Month_Year",
      y="Count",
      color=confirmation_col,
      barmode="group",  # Use 'stack' for stacked bars or 'group' for side-by-side
      text="Count",
      title="Monthly Confirmation Status Breakdown",
      labels={"Month_Year": "Month", confirmation_col: "Confirmation Received"},
  )
  fig_monthly_conf.update_xaxes(type="category")
  st.plotly_chart(fig_monthly_conf, use_container_width=True)


# ---------------- MONTHLY CATEGORY ANALYSIS ---------------- #
category_col = next(
    (col for col in df.columns if "category" in col.lower()), None
)

if category_col:
  st.subheader(" Monthly Category Breakdown")

  # Group by Month and Category
  monthly_cat = (
      df_filtered.groupby(["Month_Year", category_col], sort=False)
      .size()
      .reset_index(name="Count")
  )

  # Plot Stacked/Grouped Bar Chart
  fig_monthly_cat = px.bar(
      monthly_cat,
      x="Month_Year",
      y="Count",
      color=category_col,
      barmode="stack",  # Stacked bars work great for category breakdown
      text="Count",
      title="Monthly Category Breakdown",
      labels={"Month_Year": "Month", category_col: "Category"},
  )
  fig_monthly_cat.update_xaxes(type="category")
  st.plotly_chart(fig_monthly_cat, use_container_width=True)

# ---------------- RAW DATA ---------------- #
st.subheader(" Raw Data")
# Overwrite the date column in raw view with the formatted string date
df_display = df_filtered.copy()
df_display[date_col] = df_display["Formatted Date"]
df_display = df_display.drop(columns=["Formatted Date"])

st.dataframe(df_display, use_container_width=True)
