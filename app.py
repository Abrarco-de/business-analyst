import streamlit as st
import pandas as pd
import plotly.express as px
import os
from sahm_engine import configure_dual_engines, process_business_data, get_ai_response

# 1. Page Config
st.set_page_config(page_title="Sahm BI | Intelligence", page_icon="📈", layout="wide")

# SAHM BRAND COLORS
SAHM_BLUE = "#1E3A8A"
SAHM_GREEN = "#10B981"
SAHM_BG = "#F3F4F6"

# 2. FORCE UI THEME (Fixes the "White Issue")
st.markdown(f"""
    <style>
    /* Force background color */
    .stApp {{
        background-color: {SAHM_BG};
    }}
    /* Style the KPI cards */
    [data-testid="stMetricValue"] {{
        color: {SAHM_BLUE} !important;
        font-weight: bold;
    }}
    div[data-testid="stMetric"] {{
        background-color: white;
        border: 1px solid #E5E7EB;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    /* Fix Header Colors */
    h1, h2, h3, p {{
        color: {SAHM_BLUE} !important;
    }}
    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background-color: white !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. SMARTER LOGO LOADER
# This looks for logo.png, logo.jpg, or logo.jpeg automatically
def load_logo():
    possible_names = ["logo.png", "logo.jpg", "logo.jpeg", "Logo.png"]
    for name in possible_names:
        if os.path.exists(name):
            return name
    return None

found_logo = load_logo()

# Header Section
col_logo, col_text = st.columns([1, 5])
with col_logo:
    if found_logo:
        st.image(found_logo, width=150)
    else:
        st.markdown(f"<h1 style='font-size: 100px; margin:0;'>🏹</h1>", unsafe_allow_html=True)

with col_text:
    st.markdown(f"<h1 style='margin-bottom:0;'>Sahm BI — سهم للذكاء الأعمال</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:20px; margin-top:0; color:#4B5563 !important;'>Strategic Enterprise Analytics Platform</p>", unsafe_allow_html=True)

# --- START APP LOGIC ---

if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))

if st.session_state.m is None:
    st.divider()
    st.markdown("### 📥 Step 1: Upload Your Data")
    up = st.file_uploader("", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = process_business_data(g_client, raw)
        if "error" in m: st.error(m["error"])
        else:
            st.session_state.m = m
            st.rerun()
else:
    m = st.session_state.m
    
    with st.sidebar:
        st.markdown(f"### 🏹 Sahm Control")
        if st.button("🗑️ Reset Application", use_container_width=True):
            st.session_state.m = None
            st.session_state.chat = []
            st.rerun()
        st.divider()
        st.caption("Connected to Sahm AI v1.0")

    # --- KPI DASHBOARD ---
    st.markdown("### 🏦 Financial Summary")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Sales", f"{m.get('total_revenue', 0):,.0f} SAR")
    k2.metric("Total Profit", f"{m.get('total_profit', 0):,.0f} SAR")
    k3.metric("Units Sold", f"{m.get('total_units', 0):,}")
    k4.metric("VAT (15%)", f"{m.get('vat_due', 0):,.0f} SAR")

    # --- ANALYSIS ---
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"<h3 style='color:red !important;'>📉 Low Margin Items</h3>", unsafe_allow_html=True)
        for item in m.get('bot_margin_list', []): st.error(item)
    with col_b:
        st.markdown(f"<h3 style='color:{SAHM_GREEN} !important;'>📈 High Margin Items</h3>", unsafe_allow_html=True)
        for item in m.get('top_margin_list', []): st.success(item)

    # --- TREND CHART ---
    if m.get('trend_data'):
        st.divider()
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Month', 'Sales'])
        fig = px.line(tdf, x='Month', y='Sales', title="Sahm BI Revenue Trend", markers=True)
        fig.update_traces(line_color=SAHM_BLUE, marker=dict(color=SAHM_GREEN, size=10))
        st.plotly_chart(fig, use_container_width=True)

    # --- FLOATING CHAT ---
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px;}</style>""", unsafe_allow_html=True)
    with st.popover("💬 Ask Sahm AI Consultant"):
        st.info("Ask about VAT, Sales, or City performance.")
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Ask Sahm BI..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()
