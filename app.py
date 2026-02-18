import streamlit as st
import pandas as pd
import plotly.express as px
import os
from Truemetrics import configure_dual_engines, process_business_data, get_ai_response

# 1. Page Config
st.set_page_config(page_title="TrueMetrics | Precision BI", page_icon="🎯", layout="wide")

# TRUEMETRICS BRAND COLORS (Matched to Logo)
DARK_BG = "#0B0F19"      # Rich Dark Background
CARD_BG = "#161B28"      # Slate Card Background
TM_BLUE = "#2563EB"      # Precision Blue
TM_LIME = "#A3E635"      # High-Visibility Lime
TEXT_MAIN = "#F1F5F9"

# 2. PREMIUM DARK THEME CSS
st.markdown(f"""
    <style>
    /* Global App Styling */
    .stApp {{
        background-color: {DARK_BG};
        color: {TEXT_MAIN};
    }}
    /* Metric Cards */
    div[data-testid="stMetric"] {{
        background-color: {CARD_BG};
        border: 1px solid #1E293B;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }}
    [data-testid="stMetricValue"] {{
        color: {TM_LIME} !important;
        font-weight: 800 !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: #94A3B8 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    /* Headers & Text */
    h1, h2, h3, p {{
        color: {TEXT_MAIN} !important;
        font-family: 'Inter', sans-serif;
    }}
    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background-color: {CARD_BG} !important;
        border-right: 1px solid #1E293B;
    }}
    /* Chat Popover */
    .stPopover button {{
        background-color: {TM_BLUE} !important;
        color: white !important;
        border: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. LOGO LOADER
def load_logo():
    for name in ["logo.png", "logo.jpg", "logo.jpeg"]:
        if os.path.exists(name): return name
    return None

found_logo = load_logo()

# Header Section
col_logo, col_text = st.columns([1, 4])
with col_logo:
    if found_logo:
        st.image(found_logo, width=180)
    else:
        st.markdown(f"<h1 style='font-size: 80px; margin:0;'>🎯</h1>", unsafe_allow_html=True)

with col_text:
    st.markdown(f"<h1 style='margin-bottom:0; font-size: 50px; font-weight: 800;'>TrueMetrics</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:16px; color:{TM_BLUE} !important; font-weight: 600; letter-spacing: 3px;'>PRECISION IN EVERY DATA POINT</p>", unsafe_allow_html=True)

# --- ENGINE INITIALIZATION ---

if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))

if st.session_state.m is None:
    st.divider()
    st.markdown("### 📥 System Initialization: Upload Data")
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
        st.markdown("### 🛠️ System Control")
        if st.button("🗑️ Clear Analytics Cache", use_container_width=True):
            st.session_state.m = None
            st.session_state.chat = []
            st.rerun()
        st.divider()
        st.info("TrueMetrics Engine: Online")

    # --- KPI DASHBOARD ---
    st.subheader("📊 Performance Matrix")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Revenue", f"{m.get('total_revenue', 0):,.0f} SAR")
    k2.metric("Net Profit", f"{m.get('total_profit', 0):,.0f} SAR")
    k3.metric("Transaction Vol.", f"{m.get('total_units', 0):,}")
    k4.metric("VAT Liability", f"{m.get('vat_due', 0):,.0f} SAR")

    st.divider()

    # --- ANALYSIS GRID ---
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"### 📉 Low Margin Alerts")
        for item in m.get('bot_margin_list', []): 
            st.markdown(f"<div style='background-color:#450a0a; color:#fecaca; padding:12px; border-radius:8px; margin-bottom:8px; border-left:4px solid red;'>{item}</div>", unsafe_allow_html=True)
    with col_b:
        st.markdown(f"### 📈 Peak Margin Items")
        for item in m.get('top_margin_list', []): 
            st.markdown(f"<div style='background-color:#064e3b; color:#dcfce7; padding:12px; border-radius:8px; margin-bottom:8px; border-left:4px solid {TM_LIME};'>{item}</div>", unsafe_allow_html=True)

    # --- TRUE-VISUAL TREND ---
    if m.get('trend_data'):
        st.divider()
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Month', 'Sales'])
        fig = px.line(tdf, x='Month', y='Sales', title="Strategic Growth Trend", markers=True)
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color=TEXT_MAIN,
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="#1E293B")
        )
        fig.update_traces(line_color=TM_BLUE, line_width=4, marker=dict(color=TM_LIME, size=10, line=dict(width=2, color=TEXT_MAIN)))
        st.plotly_chart(fig, use_container_width=True)

    # --- FLOATING CHAT BOT ---
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px;}</style>""", unsafe_allow_html=True)
    with st.popover("💬 Talk to TrueMetrics AI"):
        st.markdown(f"<h4 style='color:{TM_BLUE};'>Precision Consultant</h4>", unsafe_allow_html=True)
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Analyze performance..."):
            st.session_state.chat.append({"role": "user", "content": p})
            # Ensure the engine still uses TrueMetrics persona
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()

