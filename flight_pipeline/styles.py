"""
Styles module for Flight Data Pipeline Dashboard.
Defines design tokens and injects compact, scoped CSS resets.
"""

import streamlit as st

CSS_TOKENS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg: #0E1116;
    --surface: #151A21;
    --surface-2: #1B222B;
    --border: #242C37;
    --text: #E6EAF0;
    --text-muted: #8A94A3;
    --accent: #4C9AFF;
    --ok: #3FB950;
    --warn: #D29922;
    --bad: #F85149;
}

/* Base resets & typography */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header[data-testid="stHeader"], .stDeployButton {
    display: none !important;
}

/* Number formatting */
.tabular-nums {
    font-family: 'JetBrains Mono', monospace !important;
    font-variant-numeric: tabular-nums !important;
}

/* Header Specs */
.app-header {
    margin-bottom: 20px;
}
.app-title {
    font-size: 24px;
    font-weight: 600;
    color: var(--text);
    margin: 0;
    line-height: 1.2;
    letter-spacing: -0.01em;
}
.app-subtitle {
    font-size: 13px;
    color: var(--text-muted);
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}
.status-dot.ok { background-color: var(--ok); }
.status-dot.warn { background-color: var(--warn); }
.status-dot.bad { background-color: var(--bad); }

/* KPI Cards - 4 identical height tiles */
.kpi-card {
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px 16px;
    min-height: 84px;
    height: 84px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.kpi-label {
    font-size: 12px;
    font-weight: 400;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.kpi-value {
    font-size: 28px;
    font-weight: 600;
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
    display: flex;
    align-items: baseline;
    gap: 4px;
}
.kpi-unit {
    font-size: 13px;
    font-weight: 400;
    color: var(--text-muted);
    font-family: 'Inter', sans-serif;
}

/* Sidebar Layout */
.sidebar-heading {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-muted);
    margin-top: 16px;
    margin-bottom: 8px;
}
.sidebar-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 13px;
    padding: 4px 0;
}
.sidebar-label {
    color: var(--text-muted);
}
.sidebar-val {
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
    font-weight: 500;
}

/* Underline Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 24px !important;
    background-color: transparent !important;
    padding: 0 !important;
    border: none !important;
    border-bottom: 1px solid var(--border) !important;
    border-radius: 0 !important;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    height: 40px !important;
    border: none !important;
    background-color: transparent !important;
    color: var(--text-muted) !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 0 4px !important;
    border-bottom: 2px solid transparent !important;
}

[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--text) !important;
    border-bottom: 2px solid var(--accent) !important;
    background-color: transparent !important;
}

/* Sidebar Button */
[data-testid="stSidebar"] button {
    background-color: var(--surface-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    height: 36px !important;
}
[data-testid="stSidebar"] button:hover {
    border-color: var(--accent) !important;
}
</style>
"""


def inject_css():
    """Injects design tokens and custom dashboard stylesheet."""
    st.markdown(CSS_TOKENS, unsafe_allow_html=True)
