import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Error Analytics Dashboard", layout="wide")
st.title(" Error Analytics Dashboard")

url = "https://docs.google.com/spreadsheets/d/1IihQE0Myys72Ezxhk3OA_kdlmfsjZ2ijIhqTAhYNRYA/export?format=csv&gid=0"


def load_data():
  df = pd.read_csv(url, header=2)
  df.columns = df.columns.str.strip()
  return df


df = load_data()

# Identify Date column
date_col = next(
    (col for col in df.columns if "date" in str(col).lower()), None
)

if date_col is None:
  st.error("Date column not found.")
  st.stop()

# Robust Date Parsing
df[date_col] = df[date_col].astype(str).str.strip()
df[date_col] = pd.to_datetime(
    df[date_col], format="mixed", dayfirst=True, errors="coerce"
)
df = df.dropna(subset=[date_col])
df["Formatted Date"] = df[date_col].dt.strftime("%Y-%m-%d")

# ---------------- SIDEBAR FILTERS ---------------- #
st.sidebar.header("Filters")

data_min_date = df[date_col].min().date()
data_max_date = df[date_col].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(data_min_date, data_max_date),
    min_value=data_min_date,
    max_value=data_max_date,
    key="date_range_picker_v6",
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

# Create Month Year column for grouping and filtering
df_filtered["Month_Year"] = df_filtered[date_col].dt.strftime("%b %Y")

# ---------------- 1. MONTH-WISE ERROR COUNT CHART ---------------- #
monthly_errors = (
    df_filtered.groupby("Month_Year", sort=False)
    .size()
    .reset_index(name="Error Count")
)
monthly_order = (
    df_filtered.groupby("Month_Year")[date_col]
    .min()
    .sort_values()
    .index.tolist()
)

st.subheader(" Month-wise Error Count")
st.caption(
    "💡 *Click on any bar in the chart below to filter the entire dashboard by"
    " that month!*"
)

fig_month = px.bar(
    monthly_errors,
    x="Month_Year",
    y="Error Count",
    text="Error Count",
    color="Error Count",
    category_orders={"Month_Year": monthly_order},
    title="Month-wise Error Analysis",
)
fig_month.update_xaxes(type="category")
fig_month.update_layout(
    xaxis_title="Month",
    yaxis_title="Error Count",
    clickmode="event+select",
)

selected_month_event = st.plotly_chart(
    fig_month,
    use_container_width=True,
    on_select="rerun",
    key="monthly_bar_chart",
)

# ---------------- FILTER DASHBOARD BY CLICKED MONTH ---------------- #
selected_month = None
if selected_month_event and "selection" in selected_month_event:
  points = selected_month_event["selection"].get("points", [])
  if points:
    selected_month = points[0].get("x")

if selected_month:
  st.info(
      f" Selected Month Filter: **{selected_month}** (Click anywhere on chart"
      " background to reset filter)"
  )
  df_display_filtered = df_filtered[
      df_filtered["Month_Year"] == selected_month
  ].copy()
else:
  df_display_filtered = df_filtered.copy()
# ---------------- 2. FINANCIAL QUARTERLY ERROR ANALYSIS ---------------- #
if error_by_col:
  st.subheader(" Quarterly Error Analysis (Person vs Month)")

  # Helper function to compute Financial Quarter (Q1: Apr-Jun, Q2: Jul-Sep, Q3: Oct-Dec, Q4: Jan-Mar)
  def get_fq(dt):
    month = dt.month
    year = dt.year
    if month in [4, 5, 6]:
      return f"FY{str(year)[2:]}-{str(year+1)[2:]} Q1 (Apr-Jun)"
    elif month in [7, 8, 9]:
      return f"FY{str(year)[2:]}-{str(year+1)[2:]} Q2 (Jul-Sep)"
    elif month in [10, 11, 12]:
      return f"FY{str(year)[2:]}-{str(year+1)[2:]} Q3 (Oct-Dec)"
    else: # 1, 2, 3
      return f"FY{str(year-1)[2:]}-{str(year)[2:]} Q4 (Jan-Mar)"

  df_display_filtered["FQ"] = df_display_filtered[date_col].apply(get_fq)

  # Group by Financial Quarter, Person, and Month
  fq_list = sorted(df_display_filtered["FQ"].unique())
  selected_fq = st.selectbox(
      "Select Financial Quarter:",
      options=["All Quarters"] + fq_list,
      key="fq_selector",
  )

  if selected_fq != "All Quarters":
    df_fq = df_display_filtered[df_display_filtered["FQ"] == selected_fq]
  else:
    df_fq = df_display_filtered

  # Aggregate counts per Person by Month
  fq_grouped = (
      df_fq.groupby([error_by_col, "Month_Year"])
      .size()
      .reset_index(name="Error Count")
  )
  fq_grouped.columns = ["Person", "Month", "Error Count"]

  fig_fq = px.bar(
      fq_grouped,
      x="Person",
      y="Error Count",
      color="Month",
      barmode="group",  # Use "stack" if you prefer stacked bars per person
      text="Error Count",
      title="Errors per Person by Month (Financial Quarter View)",
  )

  fig_fq.update_layout(
      xaxis_title="Person", yaxis_title="Error Count", legend_title="Month"
  )
  st.plotly_chart(fig_fq, use_container_width=True)
# ---------------- 3. ERROR BY CHART (FLEXIBLE COLUMN MATCHING) ---------------- #
error_by_col = next(
    (col for col in df.columns if "error by" in col.lower()), None
)

if error_by_col:
  st.subheader(" Error By")
  error_by = (
      df_display_filtered[error_by_col]
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
      title="Errors By Person",
  )
  st.plotly_chart(fig1, use_container_width=True)
else:
  # Helpful fallback message if the column name cannot be detected
  st.warning(
      "Could not detect 'Error By' column. Available columns:"
      f" {list(df.columns)}"
  )

# ---------------- 4. CONFIRMATION RECEIVED CHART ---------------- #
confirmation_col = next(
    (col for col in df.columns if "confirmation" in col.lower()), None
)
if confirmation_col:
  st.subheader(" Confirmation Received From Person Who Made Error")
  confirmation = (
      df_display_filtered[confirmation_col]
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

# ---------------- 5. CATEGORY ANALYSIS CHART ---------------- #
category_col = next(
    (col for col in df.columns if "category" in col.lower()), None
)
if category_col:
  st.subheader(" Category Analysis")
  category = (
      df_display_filtered[category_col]
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
      title="Category-wise Error Analysis",
  )
  st.plotly_chart(fig3, use_container_width=True)

# ---------------- 6. RAW DATA ---------------- #
st.subheader(" Raw Data")
df_display = df_display_filtered.copy()
df_display[date_col] = df_display["Formatted Date"]
df_display = df_display.drop(
    columns=["Formatted Date", "Month_Year"], errors="ignore"
)

st.dataframe(df_display, use_container_width=True)
