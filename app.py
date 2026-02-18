import streamlit as st
import pandas as pd
import plotly.express as px
import os
from sahm_engine import configure_dual_engines, process_business_data, get_ai_response

# 1. Page Config
st.set_page_config(page_title="Sahm BI | Premium", page_icon="📈", layout="wide")

# SAHM PREMIUM COLORS
DARK_BG = "#0F172A"      # Deep Navy/Dark
CARD_BG = "#1E293B"      # Lighter Slate for cards
SAHM_BLUE = "#3B82F6"    # Vibrant Neon Blue
SAHM_GREEN = "#10B981"   # Vibrant Neon Green
TEXT_WHITE = "#F8FAFC"

# 2. PREMIUM DARK CSS
st.markdown(f"""
    <style>
    /* Main Background */
    .stApp {{
        background-color: {DARK_BG};
        color: {TEXT_WHITE};
    }}
    /* Professional Metric Cards */
    div[data-testid="stMetric"] {{
        background-color: {CARD_BG};
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }}
    [data-testid="stMetricValue"] {{
        color: {SAHM_GREEN} !important;
        font-family: 'Inter', sans-serif;
    }}
    [data-testid="stMetricLabel"] {{
        color: {TEXT_WHITE} !important;
        font-size: 16px !important;
    }}
    /* Sidebar Dark Mode */
    section[data-testid="stSidebar"] {{
        background-color: {CARD_BG} !important;
        border-right: 1px solid #334155;
    }}
    /* Titles & Headers */
    h1, h2, h3, p, span {{
        color: {TEXT_WHITE} !important;
    }}
    /* Chat Popover Styling */
    .stPopover button {{
        background-color: {SAHM_BLUE} !important;
        color: white !important;
        border-radius: 50px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. LOGO LOADER
def load_logo():
    possible_names = ["logo.png", "logo.jpg", "logo.jpeg", "Logo.png"]
    for name in possible_names:
        if os.path.exists(name): return name
    return None

found_logo = load_logo()

# Header Section
col_logo, col_text = st.columns([1, 5])
with col_logo:
    if found_logo:
        st.image(found_logo, width=150)
    else:
        st.markdown(f"<h1 style='font-size: 80px; margin:0;'>🏹</h1>", unsafe_allow_html=True)

with col_text:
    st.markdown(f"<h1 style='margin-bottom:0; font-size: 45px;'>Sahm BI</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:20px; color:{SAHM_BLUE} !important; letter-spacing: 2px;'>ENTERPRISE INTELLIGENCE UNIT</p>", unsafe_allow_html=True)

# --- START APP LOGIC ---

if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))

if st.session_state.m is None:
    st.divider()
    st.markdown("### 📥 Initialize Analytics System")
    up = st.file_uploader("Upload Transaction Records", type=["csv", "xlsx"])
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
        st.markdown(f"### 🏹 Sahm Command")
        if st.button("🗑️ Reset Analytics", use_container_width=True):
            st.session_state.m = None
            st.session_state.chat = []
            st.rerun()
        st.divider()
        st.success("System Online: AI Consultant Connected")

    # --- KPI DASHBOARD ---
    st.subheader("🏦 Financial Overview")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Sales", f"{m.get('total_revenue', 0):,.0f} SAR")
    k2.metric("Net Profit", f"{m.get('total_profit', 0):,.0f} SAR")
    k3.metric("Volume", f"{m.get('total_units', 0):,}")
    k4.metric("VAT (15%)", f"{m.get('vat_due', 0):,.0f} SAR")

    st.divider()

    # --- ANALYSIS ---
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"### 📉 Bottom Performers")
        for item in m.get('bot_margin_list', []): 
            st.markdown(f"<div style='background-color:#7F1D1D; color:white; padding:10px; border-radius:5px; margin-bottom:5px;'>{item}</div>", unsafe_allow_html=True)
    with col_b:
        st.markdown(f"### 📈 Top Performers")
        for item in m.get('top_margin_list', []): 
            st.markdown(f"<div style='background-color:#064E3B; color:white; padding:10px; border-radius:5px; margin-bottom:5px;'>{item}</div>", unsafe_allow_html=True)

    # --- TREND CHART (Premium Dark Theme) ---
    if m.get('trend_data'):
        st.divider()
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Month', 'Sales'])
        fig = px.line(tdf, x='Month', y='Sales', title="Strategic Revenue Growth", markers=True)
        
        # Adjusting Plotly colors for Dark Mode
        fig.update_layout(
            plot_bgcolor=CARD_BG,
            paper_bgcolor=DARK_BG,
            font_color=TEXT_WHITE,
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="#334155")
        )
        fig.update_traces(line_color=SAHM_BLUE, line_width=4, marker=dict(color=SAHM_GREEN, size=12))
        st.plotly_chart(fig, use_container_width=True)

    # --- CHAT POPOVER ---
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px;}</style>""", unsafe_allow_html=True)
    with st.popover("💬 AI Business Strategist"):
        st.markdown(f"<h4 style='color:{SAHM_BLUE};'>Sahm Intelligence</h4>", unsafe_allow_html=True)
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Analyze these results..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()

