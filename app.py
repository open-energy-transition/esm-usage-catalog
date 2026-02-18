# app.py
from __future__ import annotations

import re
from pathlib import Path
import pandas as pd
import streamlit as st

# ----------------------------
# App config & styling
# ----------------------------
APP_NAME = "Grid Operators Modelling Usage Explorer"
CSV_FILENAME = "national-electricity-ecosystem-2026-02-16.csv-curated.csv"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
.stApp {
  background: radial-gradient(1200px circle at 10% 0%, rgba(255, 215, 0, 0.10), transparent 40%),
              radial-gradient(1000px circle at 90% 10%, rgba(0, 136, 255, 0.08), transparent 35%),
              linear-gradient(180deg, rgba(250,250,252,1) 0%, rgba(245,247,250,1) 100%);
}
.card {
  padding: 16px 16px 12px 16px;
  border-radius: 18px;
  background: rgba(255,255,255,0.75);
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 8px 24px rgba(0,0,0,0.06);
}
.card h3 { margin: 0 0 6px 0; font-weight: 700; }
.card p  { margin: 0; opacity: 0.8; }
.kpi {
  font-size: 28px;
  font-weight: 800;
  line-height: 1.1;
  margin-top: 2px;
}
.pill {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(0,0,0,0.06);
  font-size: 12px;
  margin-right: 6px;
  margin-bottom: 6px;
}
a { text-decoration: none; }
a:hover { text-decoration: underline; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------
# Schema helpers
# ----------------------------
EXPECTED_COLUMNS = [
    "country_label",
    "institution_name",
    "official_website",
    "tool_name",
    "tool_category",
    "use_case",
    "evidence_strength",
    "source_type",
    "source_title",
    "source_date",
    "source_link",
    "exact_snippet_or_quote",
    "why_it_supports_the_claim",
    "notes",
]


def normalize_columns(cols):
    norm = []
    for c in cols:
        c2 = str(c).strip()
        c2 = re.sub(r"\s+", "_", c2)
        norm.append(c2)
    return norm


@st.cache_data(show_spinner=False)
def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path.resolve()}")

    df = pd.read_csv(path, engine="python", sep=None, dtype=str)

    df.columns = normalize_columns(df.columns)

    for c in EXPECTED_COLUMNS:
        if c not in df.columns:
            df[c] = ""

    for c in EXPECTED_COLUMNS:
        df[c] = df[c].fillna("").astype(str).str.strip()

    return df


def uniq_sorted(series: pd.Series):
    vals = [v for v in series.dropna().astype(str).unique().tolist() if v.strip()]
    return sorted(vals, key=lambda x: x.lower())


def safe_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, flags=re.I):
        return "https://" + url
    return url


def contains_text_row(row: pd.Series, needle: str) -> bool:
    if not needle:
        return True
    needle_l = needle.lower()
    hay = " | ".join(str(row.get(c, "")) for c in EXPECTED_COLUMNS).lower()
    return needle_l in hay


def as_link(url: str, label: str) -> str:
    if not url:
        return ""
    return f"[{label}]({url})"


# ----------------------------
# Load data
# ----------------------------
st.title(f"⚡ {APP_NAME}")
st.caption("Explore tool usage, institutions, evidence, and sources — powered by your curated CSV.")

csv_path = Path(__file__).parent / CSV_FILENAME
try:
    df = load_csv(csv_path)
except Exception as e:
    st.error(
        "Could not load the CSV. Make sure the file is in the same folder as this script "
        f"and named exactly: {CSV_FILENAME}"
    )
    st.exception(e)
    st.stop()

# ----------------------------
# Sidebar filters
# ----------------------------
st.sidebar.header("Filters")

countries = ["All"] + uniq_sorted(df["country_label"])
categories = ["All"] + uniq_sorted(df["tool_category"])
evidence = ["All"] + uniq_sorted(df["evidence_strength"])
source_types = ["All"] + uniq_sorted(df["source_type"])

sel_country = st.sidebar.selectbox("Country", countries, index=0)
sel_category = st.sidebar.selectbox("Tool category", categories, index=0)
sel_evidence = st.sidebar.selectbox("Evidence strength", evidence, index=0)
sel_source_type = st.sidebar.selectbox("Source type", source_types, index=0)

text_query = st.sidebar.text_input(
    "Search text (any column)",
    value="",
    placeholder="e.g., dispatch, balancing, market coupling…",
)

# Tool distribution controls
st.sidebar.header("Tool distribution chart")
top_n = st.sidebar.slider("Show top N tools", min_value=5, max_value=50, value=20, step=1)
include_unknown_tools = st.sidebar.checkbox("Include empty/unknown tool_name", value=False)

# ----------------------------
# Apply filters
# ----------------------------
f = df.copy()

if sel_country != "All":
    f = f[f["country_label"] == sel_country]
if sel_category != "All":
    f = f[f["tool_category"] == sel_category]
if sel_evidence != "All":
    f = f[f["evidence_strength"] == sel_evidence]
if sel_source_type != "All":
    f = f[f["source_type"] == sel_source_type]

if text_query.strip():
    mask = f.apply(lambda r: contains_text_row(r, text_query.strip()), axis=1)
    f = f[mask]

# ----------------------------
# KPI cards
# ----------------------------
col1, col2, col3, col4 = st.columns(4)

total_rows = len(df)
filtered_rows = len(f)
unique_countries = f["country_label"].replace("", pd.NA).dropna().nunique()
unique_institutions = f["institution_name"].replace("", pd.NA).dropna().nunique()
unique_tools = f["tool_name"].replace("", pd.NA).dropna().nunique()

with col1:
    st.markdown(
        f"""
        <div class="card">
          <h3>Rows</h3>
          <div class="kpi">{filtered_rows:,}</div>
          <p>of {total_rows:,} total</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""
        <div class="card">
          <h3>Countries</h3>
          <div class="kpi">{unique_countries:,}</div>
          <p>in current selection</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""
        <div class="card">
          <h3>Institutions</h3>
          <div class="kpi">{unique_institutions:,}</div>
          <p>in current selection</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col4:
    st.markdown(
        f"""
        <div class="card">
          <h3>Tools</h3>
          <div class="kpi">{unique_tools:,}</div>
          <p>unique tool_name</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# ----------------------------
# Tool name distribution chart
# ----------------------------
st.subheader("Tool name distribution")

tool_series = f["tool_name"].copy()
if include_unknown_tools:
    tool_series = tool_series.replace("", "Unknown")
else:
    tool_series = tool_series[tool_series.str.strip() != ""]

tool_counts = (
    tool_series.value_counts()
    .head(top_n)
    .rename_axis("tool_name")
    .reset_index(name="count")
)

if tool_counts.empty:
    st.info("No tool_name values to plot for the current filters.")
else:
    st.caption(f"Top {min(top_n, len(tool_counts))} tools by record count (based on current filters).")
    st.bar_chart(tool_counts.set_index("tool_name")["count"])

st.write("")

# ----------------------------
# Data table
# ----------------------------
st.subheader("Records")

display = f.copy()
display["official_website"] = display["official_website"].apply(safe_url)
display["source_link"] = display["source_link"].apply(safe_url)

display_cols = [
    "country_label",
    "institution_name",
    "tool_name",
    "tool_category",
    "use_case",
    "evidence_strength",
    "source_type",
    "source_title",
    "source_date",
    "source_link",
    "official_website",
    "notes",
]
display_cols = [c for c in display_cols if c in display.columns]

with st.expander("Table options", expanded=False):
    chosen_cols = st.multiselect(
        "Columns to show",
        options=display_cols,
        default=display_cols[:10],
    )

table_df = display[chosen_cols].copy()
if "source_link" in table_df.columns:
    table_df["source_link"] = table_df["source_link"].apply(lambda u: as_link(u, "Source"))
if "official_website" in table_df.columns:
    table_df["official_website"] = table_df["official_website"].apply(lambda u: as_link(u, "Website"))

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
)

csv_bytes = f.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download filtered CSV",
    data=csv_bytes,
    file_name="filtered_grid_operators_modelling_usage.csv",
    mime="text/csv",
)

