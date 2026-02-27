# app.py
from __future__ import annotations

import re
from pathlib import Path
import pandas as pd
import streamlit as st

import plotly.express as px

from streamlit_option_menu import option_menu

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


# ----------------------------
# Top-right Dark Mode Toggle
# ----------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

top_left, top_right = st.columns([0.95, 0.05])

with top_right:
    if st.session_state.dark_mode:
        st.button("☀️", on_click=toggle_theme, help="Switch to light mode")
    else:
        st.button("🌙", on_click=toggle_theme, help="Switch to dark mode")
        
# ----------------------------
# Dynamic Theme Styling
# ----------------------------
if st.session_state.dark_mode:
    CUSTOM_CSS = """
    <style>
    /* App background & default text */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }

    /* =========================
       CARDS / KPI BOXES
    ========================== */
    .card {
        padding: 16px 16px 12px 16px;
        border-radius: 18px;
        background: #1F2937;
        border: 1px solid #333;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }
    .card h3 { margin: 0 0 6px 0; font-weight: 700; }
    .card p  { margin: 0; opacity: 0.8; }
    .kpi {
        font-size: 28px;
        font-weight: 800;
        line-height: 1.1;
        margin-top: 2px;
    }

    a { color: #4da6ff; }

    /* =========================
       DOWNLOAD BUTTON
    ========================== */
    .stDownloadButton > button {
        background-color: #2563EB !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
    }
    .stDownloadButton > button:hover {
        background-color: #1E40AF !important;
        color: white !important;
    }

    /* =========================
       TABS (Dark Mode)
    ========================== */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #161B22 !important;
        border-radius: 14px !important;
        padding: 6px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #A0A0A0 !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        padding: 8px 16px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
    }

    /* =========================
       RADIO BUTTONS
    ========================== */
    /* Radio group title (e.g., "Select map metric:") */
    .stRadio > label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* Each radio option text ("Total Records", "Unique Tools") */
    div[data-baseweb="radio"] span[class*="radioLabel"] {
        color: #FFFFFF !important;
    }

    /* Outer circle of the radio button */
    div[data-baseweb="radio"] div[role="radio"] {
        border-color: #FFFFFF !important;
    }

    /* Inner dot for checked radio */
    div[data-baseweb="radio"] input:checked + div {
        background-color: #2563EB !important;
        border-color: #2563EB !important;
    }

    /* =========================
       TABLE (st.dataframe) DARK MODE
    ========================== */
    div[data-testid="stDataFrame"] div[role="grid"] {
        background-color: #1F2937 !important;
        color: #E5E7EB !important;
    }
    div[data-testid="stDataFrame"] div[role="columnheader"] {
        background-color: #111827 !important;
        color: #E5E7EB !important;
    }
    div[data-testid="stDataFrame"] div[role="row"] {
        color: #E5E7EB !important;
    }

    </style>
    """

else:
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
      background: rgba(255,255,255,0.85);
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

    a { text-decoration: none; }
    a:hover { text-decoration: underline; }

    /* ✅ STYLE DOWNLOAD BUTTON FOR LIGHT MODE */
    .stDownloadButton > button {
        background-color: #1f77ff !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    .stDownloadButton > button:hover {
        background-color: #1559c1 !important;
    }

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
          <h3>Applications</h3>
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
# MAIN ANALYTICAL TABS
# ----------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🌍 Geographic Analysis",
    "🛠 Tool & Category Analysis",
    "🏛 Institutions",
    "📄 Records & Export"
])

with tab1:

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

    if not tool_counts.empty:
        fig = px.bar(
            tool_counts,
            x="count",
            y="tool_name",
            orientation="h",
            template="plotly_dark" if st.session_state.dark_mode else "plotly_white",
        )

        if st.session_state.dark_mode:
            fig.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font=dict(color="#FFFFFF"),  # axes, labels, hover text
                title=dict(
                    text="Top Tools by Record Count",
                    font=dict(color="#FFFFFF", size=20)
                ),
                yaxis=dict(autorange="reversed")
            )
        else:
            fig.update_layout(
                title=dict(
                    text="Top Tools by Record Count",
                    font=dict(color="#000000", size=20)
                ),
                yaxis=dict(autorange="reversed")
            )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tool data to display for the current filters.")
        
with tab2:

    st.subheader("Global Modelling Usage Map")

    

    map_metric = option_menu(
        menu_title=None,
        options=["Total Records", "Unique Tools"],
        orientation="horizontal",
        default_index=0,
        styles={
            "container": {"background-color": "#0E1117"},
            "nav-link": {"font-size": "16px", "color": "#FFFFFF"},
            "nav-link-selected": {"background-color": "#2563EB", "color": "white"},
        }
    )

    if map_metric == "Total Records":
        map_df = (
            f.groupby("country_label")
            .size()
            .reset_index(name="value")
        )
        color_label = "Total Records"
    else:
        map_df = (
            f.groupby("country_label")["tool_name"]
            .nunique()
            .reset_index(name="value")
        )
        color_label = "Unique Tools"

    map_df = map_df[map_df["country_label"].str.strip() != ""]

    if map_df.empty:
        st.info("No country data available for the selected filters.")
    else:
        # Choose color scale based on theme
        if st.session_state.dark_mode:
            map_scale = px.colors.sequential.Jet[1:]  # better contrast on dark
        else:
            map_scale = "Jet"

        fig = px.choropleth(
            map_df,
            locations="country_label",
            locationmode="country names",
            color="value",
            hover_name="country_label",
            color_continuous_scale=map_scale,
            labels={"value": color_label},
        )

        # Theme-specific styling
        if st.session_state.dark_mode:
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0E1117",
                plot_bgcolor="#0E1117",
                margin=dict(l=0, r=0, t=0, b=0),
                height=500,
            )
            fig.update_geos(
                bgcolor="#0E1117",
                showocean=True,
                oceancolor="#0E1117",
                lakecolor="#0E1117",
            )
        else:
            fig.update_layout(
                template="plotly_white",
                margin=dict(l=0, r=0, t=0, b=0),
                height=500,
            )

        st.plotly_chart(fig, use_container_width=True)


        
with tab3:

    colA, colB = st.columns(2)

    # Tool category distribution
    with colA:
        cat_counts = (
            f["tool_category"]
            .replace("", pd.NA)
            .dropna()
            .value_counts()
            .reset_index()
        )
        cat_counts.columns = ["tool_category", "count"]
        
        if not cat_counts.empty:
            fig_cat = px.pie(
                cat_counts,
                names="tool_category",
                values="count",
                title="Tool Category Distribution",
                template="plotly_dark" if st.session_state.dark_mode else "plotly_white",
            )

            if st.session_state.dark_mode:
                fig_cat.update_layout(
                    paper_bgcolor="#111827",
                    plot_bgcolor="#111827",
                    font=dict(color="#FFFFFF"),  # title and hover text
                    title=dict(
                        text="Tool Category Distribution",
                        font=dict(color="#FFFFFF", size=20)
                    ),
                    legend=dict(
                        font=dict(color="#FFFFFF", size=12)  # <-- legend text color
                    )
                )

            st.plotly_chart(fig_cat, use_container_width=True)

    # Evidence strength distribution
    with colB:
        ev_counts = (
            f["evidence_strength"]
            .replace("", pd.NA)
            .dropna()
            .value_counts()
            .reset_index()
        )
        ev_counts.columns = ["evidence_strength", "count"]

        if not ev_counts.empty:
            fig_ev = px.bar(
                ev_counts,
                x="evidence_strength",
                y="count",
                title="Evidence Strength Distribution",
                template="plotly_dark" if st.session_state.dark_mode else "plotly_white",
            )

            if st.session_state.dark_mode:
                fig_ev.update_layout(
                    paper_bgcolor="#111827",
                    plot_bgcolor="#111827",
                    font=dict(color="#FFFFFF"),  # All text white
                    title=dict(
                        text="Evidence Strength Distribution",
                        font=dict(color="#FFFFFF", size=20)
                    ),
                    xaxis=dict(title_font=dict(color="#FFFFFF"), tickfont=dict(color="#FFFFFF")),
                    yaxis=dict(title_font=dict(color="#FFFFFF"), tickfont=dict(color="#FFFFFF")),
                )

            st.plotly_chart(fig_ev, use_container_width=True)
            
with tab4:

    inst_counts = (
        f["institution_name"]
        .replace("", pd.NA)
        .dropna()
        .value_counts()
        .head(25)
        .reset_index()
    )
    inst_counts.columns = ["institution_name", "count"]

    if inst_counts.empty:
        st.info("No institution data available.")
    else:
        fig_inst = px.bar(
            inst_counts,
            x="count",
            y="institution_name",
            orientation="h",
            title="Top Institutions by Record Count",
            template="plotly_dark" if st.session_state.dark_mode else "plotly_white",
        )

        # Dark mode adjustments
        if st.session_state.dark_mode:
            fig_inst.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font=dict(color="#FFFFFF"),  # All text white
                title=dict(
                    text="Top Institutions by Record Count",
                    font=dict(color="#FFFFFF", size=20)
                ),
                xaxis=dict(title_font=dict(color="#FFFFFF"), tickfont=dict(color="#FFFFFF")),
                yaxis=dict(title_font=dict(color="#FFFFFF"), tickfont=dict(color="#FFFFFF")),
                height=700,
                yaxis_autorange="reversed",
            )
        else:
            fig_inst.update_layout(
                height=700,
                yaxis_autorange="reversed",
            )

        st.plotly_chart(fig_inst, use_container_width=True)
        
with tab5:

    st.subheader("Filtered Records")

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

    chosen_cols = st.multiselect(
        "Columns to show",
        options=display_cols,
        default=display_cols[:10],
    )

    table_df = display[chosen_cols].copy()

    # Convert links to markdown
    if "source_link" in table_df.columns:
        table_df["source_link"] = table_df["source_link"].apply(lambda u: as_link(u, "Source"))
    if "official_website" in table_df.columns:
        table_df["official_website"] = table_df["official_website"].apply(lambda u: as_link(u, "Website"))

    # Dark mode table styling
    if st.session_state.dark_mode:
        st.dataframe(
            table_df.style.set_properties(**{
                'background-color': '#1E1E1E',
                'color': '#FFFFFF',
                'border-color': '#333333'
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.dataframe(table_df, use_container_width=True, hide_index=True)

    # CSV download
    csv_bytes = f.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download filtered CSV",
        data=csv_bytes,
        file_name="filtered_grid_operators_modelling_usage.csv",
        mime="text/csv",
    )
