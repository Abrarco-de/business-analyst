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

# --- [ HEADER ] ---
st.markdown("<h1 style='font-size:60px; margin-bottom:0;'>TrueMetrics</h1>", unsafe_allow_html=True)
st.markdown("<div class='status-bar'>SYSTEM ACTIVE: UNIVERSAL ENGINE V2.0</div>", unsafe_allow_html=True)

# --- [ UPLOAD LOGIC ] ---
if st.session_state.m is None:
    up = st.file_uploader("Upload any Business Dataset (CSV/XLSX)", type=["csv", "xlsx"])
    if up:
        try:
            raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
            # Process and immediately store in session state
            processed_data, _ = tm.process_business_data(raw)
            if "error" in processed_data:
                st.error(processed_data["error"])
            else:
                st.session_state.m = processed_data
                st.rerun()
        except Exception as e:
            st.error(f"File Load Error: {e}")
else:
    # ACCESS DATA SAFELY
    m = st.session_state.m
    
    # KEY ERROR PREVENTION: Double check if key exists before rendering
    if 'confidence' not in m:
        st.warning("Data processing incomplete. Please re-upload the file.")
        if st.button("Reset System"):
            st.session_state.m = None
            st.rerun()
        st.stop()

    if st.sidebar.button("🗑️ Clear & Upload New"):
        st.session_state.m = None
        st.session_state.chat = []
        st.rerun()

    # --- [ KPI STRIP ] ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Volume", f"{m.get('total_revenue', 0):,.2f}")
    k2.metric("📈 Net Profit", f"{m.get('total_profit', 0):,.2f}")
    k3.metric("🎯 Margin", f"{m.get('margin_pct', 0)}%")
    k4.metric("🔮 Forecast (Avg)", f"{m.get('forecast', 0):,.2f}")

    # --- [ MAPPING INSIGHTS ] ---
    with st.expander(f"🔍 Mapping Confidence: {m['confidence']}%", expanded=False):
        st.write("Universal Mapping Results:")
        st.table(pd.DataFrame(m['mapping_preview']))

    # --- [ VISUALS ] ---
    c_top, c_risk = st.columns(2)
    with c_top:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<h4>💎 Top Segments ({m.get('loc_header', 'Category')})</h4>", unsafe_allow_html=True)
        for i in m.get('top_margins', []): st.success(i)
        st.markdown("</div>", unsafe_allow_html=True)
    with c_risk:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<h4>⚠️ Optimization Risks</h4>", unsafe_allow_html=True)
        for i in m.get('bot_margins', []): st.error(i)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- [ TREND ] ---
    if m.get('trend_data'):
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Timeline', 'Value'])
        fig = px.area(tdf, x='Timeline', y='Value', title="Chronological Trend")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- [ AI POP-OVER ] ---
    with st.popover("💬 Ask AI Consultant"):
        chat_h = st.container(height=300)
        for msg in st.session_state.chat:
            with chat_h.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Ask about your data..."):
            st.session_state.chat.append({"role": "user", "content": p})
            st.session_state.chat.append({"role": "assistant", "content": tm.get_ai_response(m_client, m, p)})
            st.rerun()
