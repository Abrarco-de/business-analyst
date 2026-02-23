import streamlit as st
import pandas as pd
import plotly.express as px
import Truemetrics as tm

# 1. STYLE & FONT
st.set_page_config(page_title="TrueMetrics | Universal", page_icon="🌐", layout="wide")
BLUE, DARK, PANEL = "#3B82F6", "#020617", "rgba(255, 255, 255, 0.03)"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&family=Inter:wght@400;500&display=swap');
    .stApp {{ background: {DARK}; color: #f8fafc; font-family: 'Inter', sans-serif; }}
    h1, h2, h3, h4 {{ font-family: 'Outfit', sans-serif !important; }}
    div[data-testid="stMetric"] {{
        background: {PANEL} !important; border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 20px !important; padding: 20px !important;
    }}
    .glass-card {{
        background: {PANEL}; border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px; padding: 25px; margin-bottom: 20px;
    }}
    .status-bar {{ padding: 10px 20px; border-radius: 50px; background: rgba(59,130,246,0.1); color: {BLUE}; font-weight: 600; font-size: 12px; display: inline-block; margin-bottom: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# 2. INIT
g_client, m_client = tm.configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))
if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# --- [ HEADER + TAGLINE ] ---
st.markdown("<h1 style='font-size:60px; margin-bottom:0;'>TrueMetrics</h1>", unsafe_allow_html=True)
st.markdown("<div class='status-bar'>SYSTEM ACTIVE: UNIVERSAL ENGINE V2.0</div>", unsafe_allow_html=True)

# --- [ UPLOAD / RESET ] ---
if st.session_state.m is None:
    up = st.file_uploader("Upload any Business Dataset (CSV/XLSX)", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = tm.process_business_data(raw)
        if "error" in m: st.error(m["error"])
        else:
            st.session_state.m = m
            st.rerun()
else:
    m = st.session_state.m
    if st.sidebar.button("🗑️ Clear & Upload New"):
        st.session_state.m = None
        st.session_state.chat = []
        st.rerun()

    # --- [ KPI STRIP ] ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Volume", f"{m['total_revenue']:,.2f}")
    k2.metric("📈 Net Profit", f"{m['total_profit']:,.2f}")
    k3.metric("🎯 Margin", f"{m['margin_pct']}%")
    k4.metric("🔮 Forecast (Avg)", f"{m['forecast']:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- [ CONFIDENCE + META ] ---
    with st.expander(f"🔍 Mapping Confidence: {m['confidence']}%", expanded=False):
        st.write("The engine automatically assigned your columns to these business logic roles:")
        st.table(pd.DataFrame(m['mapping_preview']))

    # --- [ INSIGHTS ] ---
  # --- [ INSIGHTS SECTION (Top / Risk) ] ---
    c_top, c_risk = st.columns(2)
    
    # Safely get the location header name, default to 'Segment' if not found
    loc_title = m.get('loc_header', 'Segment')
    
    with c_top:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<h4>💎 Top Segments ({loc_title})</h4>", unsafe_allow_html=True)
        
        # Safely get the list of top margins, default to empty list if not found
        top_list = m.get('top_margins', [])
        if top_list:
            for i in top_list: st.success(i)
        else:
            st.info("Analyzing top performers...")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with c_risk:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<h4>⚠️ Optimization Risks</h4>", unsafe_allow_html=True)
        
        # Safely get the list of bottom margins
        bot_list = m.get('bot_margins', [])
        if bot_list:
            for i in bot_list: st.error(i)
        else:
            st.info("Scanning for risks...")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- [ TREND CHART ] ---
    if m['trend_data']:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4>📊 Chronological Trend</h4>", unsafe_allow_html=True)
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Timeline', 'Value'])
        fig = px.area(tdf, x='Timeline', y='Value')
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=350)
        fig.update_traces(line_color=BLUE, fillcolor='rgba(59, 130, 246, 0.1)', line_width=3)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- [ FLOATING AI CHAT ] ---
    with st.popover("💬 Ask AI Data Expert"):
        st.markdown("### Intelligent Consultant")
        chat_h = st.container(height=300)
        for msg in st.session_state.chat:
            with chat_h.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Ask: 'What is the summary of this data?'"):
            st.session_state.chat.append({"role": "user", "content": p})
            st.session_state.chat.append({"role": "assistant", "content": tm.get_ai_response(m_client, m, p)})
            st.rerun()

