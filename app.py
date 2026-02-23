import streamlit as st
import pandas as pd
import plotly.express as px
import Truemetrics as tm

# --- 1. SETUP & CSS ---
st.set_page_config(page_title="TrueMetrics | Architect", page_icon="⚡", layout="wide")
BLUE, LIME, DARK, PANEL = "#3B82F6", "#A3E635", "#020617", "rgba(255, 255, 255, 0.03)"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&family=Inter:wght@400;500;600&display=swap');
    
    .stApp {{ background: {DARK}; color: #f8fafc; font-family: 'Inter', sans-serif; }}
    h1, h2, h3, h4 {{ font-family: 'Outfit', sans-serif !important; }}
    
    /* Header & Tagline */
    .hero-title {{ font-size: 56px; font-weight: 900; letter-spacing: -2px; line-height: 1; margin: 0; 
                   background: linear-gradient(135deg, #ffffff, #64748b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .tagline {{ color: {BLUE}; font-family: 'Inter'; font-weight: 600; letter-spacing: 2px; font-size: 13px; text-transform: uppercase; margin-top: 5px; margin-bottom: 25px; }}
    
    /* KPI Cards */
    div[data-testid="stMetric"] {{
        background: {PANEL} !important; border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 20px !important; padding: 20px !important;
        border-top: 3px solid {BLUE} !important;
    }}
    div[data-testid="stMetricValue"] {{ font-family: 'Outfit', sans-serif !important; font-size: 32px !important; font-weight: 700 !important; color: #fff !important; }}
    
    /* Panels */
    .glass-panel {{
        background: {PANEL}; border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px; padding: 25px; margin-bottom: 25px;
    }}
    .insight-good {{ background: rgba(163,230,53,0.1); border-left: 4px solid {LIME}; padding: 12px; border-radius: 8px; margin-bottom: 8px; font-size: 14px; }}
    .insight-bad {{ background: rgba(239,68,68,0.1); border-left: 4px solid #ef4444; padding: 12px; border-radius: 8px; margin-bottom: 8px; font-size: 14px; }}
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE INIT ---
g_client, m_client = tm.configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))
if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# ==========================================
# [ SECTION 1: HEADER + TAGLINE ]
# ==========================================
st.markdown("<h1 class='hero-title'>TrueMetrics</h1>", unsafe_allow_html=True)
st.markdown("<p class='tagline'>⚡ Precision Business Intelligence</p>", unsafe_allow_html=True)

# ==========================================
# [ SECTION 2: UPLOAD / RESET ]
# ==========================================
if st.session_state.m is None:
    up = st.file_uploader("Upload your dataset (CSV/XLSX)", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = tm.process_business_data(raw)
        if "error" in m: st.error(m["error"])
        else:
            st.session_state.m = m
            st.rerun()
else:
    m = st.session_state.m
    if st.button("🔄 Reset System"):
        st.session_state.m = None
        st.session_state.chat = []
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # [ SECTION 3: KPI STRIP (4 CARDS) ]
    # ==========================================
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Revenue", f"{m.get('total_revenue', 0):,.0f} SAR")
    k2.metric("📈 Net Profit", f"{m.get('total_profit', 0):,.0f} SAR")
    k3.metric("🎯 Profit Margin", f"{m.get('margin_pct', 0)}%")
    k4.metric("🔮 3-Month Forecast", f"{m.get('forecast', 0):,.0f} SAR")

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # [ SECTION 4: CONFIDENCE & META INFO ]
    # ==========================================
    with st.expander(f"🧬 Engine Confidence: {m.get('confidence', 0)}% (View Meta Info)", expanded=False):
        st.write(f"**Rows Analyzed:** {m.get('units', 0):,}")
        st.markdown("**Data Mapping Structure:**")
        st.table(pd.DataFrame(m.get("mapping_preview", [])))

    # ==========================================
    # [ SECTION 5: INSIGHTS (TOP / RISK) ]
    # ==========================================
    c_top, c_risk = st.columns(2)
    with c_top:
        st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
        st.markdown(f"<h4>⭐ Peak Performers</h4>", unsafe_allow_html=True)
        for item in m.get('top_margins', []):
            st.markdown(f"<div class='insight-good'><b>{item}</b></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with c_risk:
        st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
        st.markdown(f"<h4>⚠️ Margin Risks</h4>", unsafe_allow_html=True)
        for item in m.get('bot_margins', []):
            st.markdown(f"<div class='insight-bad'><b>{item}</b></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    # [ SECTION 6: TREND CHART ]
    # ==========================================
    if m.get('trend_data'):
        st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
        st.markdown(f"<h4>📊 Revenue Trajectory</h4>", unsafe_allow_html=True)
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
        fig = px.area(tdf, x='Date', y='Sales')
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=350, margin=dict(l=0,r=0,t=10,b=0))
        fig.update_traces(line_color=BLUE, fillcolor='rgba(59, 130, 246, 0.15)', line_width=4)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    # [ SECTION 7: FLOATING AI CHAT ]
    # ==========================================
    # Using Streamlit popover to create a floating-style interactive chat menu
    st.markdown("<br>", unsafe_allow_html=True)
    with st.popover("💬 Ask AI Data Expert"):
        st.markdown("#### TrueMetrics AI Consultant")
        chat_box = st.container(height=300)
        with chat_box:
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Ask a question about the data..."):
            st.session_state.chat.append({"role": "user", "content": p})
            st.session_state.chat.append({"role": "assistant", "content": tm.get_ai_response(m_client, m, p)})
            st.rerun()
