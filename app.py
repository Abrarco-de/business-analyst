import streamlit as st
import pandas as pd
import plotly.express as px
import os
from Truemetrics import configure_dual_engines, process_business_data, get_ai_response

# 1. Page Config
st.set_page_config(page_title="TrueMetrics | Precision BI", page_icon="🎯", layout="wide")

# TRUEMETRICS COLORS
DARK_BG = "#0B0F19"
CARD_BG = "#161B28"
TM_BLUE = "#2563EB"
TM_LIME = "#A3E635"
TEXT_MAIN = "#F1F5F9"

# 2. UI Styling
st.markdown(f"""
    <style>
    .stApp {{ background-color: {DARK_BG}; color: {TEXT_MAIN}; }}
    div[data-testid="stMetric"] {{
        background-color: {CARD_BG}; border: 1px solid #1E293B; padding: 20px; border-radius: 15px;
    }}
    [data-testid="stMetricValue"] {{ color: {TM_LIME} !important; font-weight: 800 !important; }}
    [data-testid="stMetricLabel"] {{ color: #94A3B8 !important; }}
    h1, h2, h3 {{ color: {TEXT_MAIN} !important; font-weight: 800; }}
    section[data-testid="stSidebar"] {{ background-color: {CARD_BG} !important; border-right: 1px solid #1E293B; }}
    .stPopover button {{ background-color: {TM_BLUE} !important; color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# 3. Initialize Engines
g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))

if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# Header
col_logo, col_text = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo.png"): st.image("logo.png", width=160)
    else: st.markdown("<h1 style='font-size: 80px; margin:0;'>🎯</h1>", unsafe_allow_html=True)

with col_text:
    st.markdown("<h1 style='margin-bottom:0; font-size: 48px;'>TrueMetrics</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{TM_BLUE}; font-weight: bold; letter-spacing: 2px;'>PRECISION IN EVERY DATA POINT</p>", unsafe_allow_html=True)

# 4. App Logic
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

# 1. Page Config
st.set_page_config(page_title="TrueMetrics | Precision BI", page_icon="🎯", layout="wide")

# TRUEMETRICS COLORS
DARK_BG = "#0B0F19"
CARD_BG = "#161B28"
TM_BLUE = "#2563EB"
TM_LIME = "#A3E635"
TEXT_MAIN = "#F1F5F9"

# 2. UI Styling
st.markdown(f"""
    <style>
    .stApp {{ background-color: {DARK_BG}; color: {TEXT_MAIN}; }}
    div[data-testid="stMetric"] {{
        background-color: {CARD_BG}; border: 1px solid #1E293B; padding: 20px; border-radius: 15px;
    }}
    [data-testid="stMetricValue"] {{ color: {TM_LIME} !important; font-weight: 800 !important; }}
    [data-testid="stMetricLabel"] {{ color: #94A3B8 !important; }}
    h1, h2, h3 {{ color: {TEXT_MAIN} !important; font-weight: 800; }}
    section[data-testid="stSidebar"] {{ background-color: {CARD_BG} !important; border-right: 1px solid #1E293B; }}
    .stPopover button {{ background-color: {TM_BLUE} !important; color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# 3. Initialize Engines
g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))

if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# Header
col_logo, col_text = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo.png"): st.image("logo.png", width=160)
    else: st.markdown("<h1 style='font-size: 80px; margin:0;'>🎯</h1>", unsafe_allow_html=True)

with col_text:
    st.markdown("<h1 style='margin-bottom:0; font-size: 48px;'>TrueMetrics</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{TM_BLUE}; font-weight: bold; letter-spacing: 2px;'>PRECISION IN EVERY DATA POINT</p>", unsafe_allow_html=True)

# 4. App Logic
if st.session_state.m is None:
    st.divider()
    up = st.file_uploader("Upload Transaction Data (CSV/Excel)", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = process_business_data(raw)
        if "error" in m: st.error(m["error"])
        else:
            st.session_state.m = m
            st.rerun()
else:
    m = st.session_state.m
    with st.sidebar:
        st.markdown("### 🛠️ Controls")
        if st.button("🗑️ Reset Session", use_container_width=True):
            st.session_state.m = None
            st.session_state.chat = []
            st.rerun()

    # Metrics
    st.subheader("🏦 Performance Matrix")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Revenue", f"{m['total_revenue']:,.0f} SAR")
    k2.metric("Net Profit", f"{m['total_profit']:,.0f} SAR")
    k3.metric("Transactions", f"{m['total_units']:,}")
    k4.metric("VAT (15%)", f"{m['vat_due']:,.0f} SAR")

    # Margin Insights
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 📉 Low Margins")
        for i in m['bot_margin_list']: st.markdown(f"<div style='background-color:#450a0a; padding:10px; border-radius:5px; margin-bottom:5px;'>{i}</div>", unsafe_allow_html=True)
    with col_b:
        st.markdown("### 📈 Peak Margins")
        for i in m['top_margin_list']: st.markdown(f"<div style='background-color:#064e3b; padding:10px; border-radius:5px; margin-bottom:5px;'>{i}</div>", unsafe_allow_html=True)

    # Trend Chart
    if m.get('trend_data'):
        st.divider()
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
        fig = px.line(tdf, x='Date', y='Sales', title="Strategic Revenue Growth")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=TEXT_MAIN, xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1E293B"))
        fig.update_traces(line_color=TM_BLUE, line_width=4, marker=dict(color=TM_LIME, size=10))
        st.plotly_chart(fig, use_container_width=True)

    # Chatbot
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px;}</style>""", unsafe_allow_html=True)
    with st.popover("💬 TrueMetrics AI"):
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        if p := st.chat_input("Analyze these metrics..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()

    # Metrics
    st.subheader("🏦 Performance Matrix")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Revenue", f"{m['total_revenue']:,.0f} SAR")
    k2.metric("Net Profit", f"{m['total_profit']:,.0f} SAR")
    k3.metric("Transactions", f"{m['total_units']:,}")
    k4.metric("VAT (15%)", f"{m['vat_due']:,.0f} SAR")

    # Margin Insights
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 📉 Low Margins")
        for i in m['bot_margin_list']: st.markdown(f"<div style='background-color:#450a0a; padding:10px; border-radius:5px; margin-bottom:5px;'>{i}</div>", unsafe_allow_html=True)
    with col_b:
        st.markdown("### 📈 Peak Margins")
        for i in m['top_margin_list']: st.markdown(f"<div style='background-color:#064e3b; padding:10px; border-radius:5px; margin-bottom:5px;'>{i}</div>", unsafe_allow_html=True)

    # Trend Chart
    if m.get('trend_data'):
        st.divider()
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
        fig = px.line(tdf, x='Date', y='Sales', title="Strategic Revenue Growth")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=TEXT_MAIN, xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1E293B"))
        fig.update_traces(line_color=TM_BLUE, line_width=4, marker=dict(color=TM_LIME, size=10))
        st.plotly_chart(fig, use_container_width=True)

    # Chatbot
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px;}</style>""", unsafe_allow_html=True)
    with st.popover("💬 TrueMetrics AI"):
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        if p := st.chat_input("Analyze these metrics..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()

