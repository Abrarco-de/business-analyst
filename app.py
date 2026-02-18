import streamlit as st
import pandas as pd
import plotly.express as px
import os
from Truemetrics import configure_dual_engines, process_business_data, get_ai_response

# 1. Page Config
st.set_page_config(page_title="TrueMetrics | Intelligence", page_icon="🎯", layout="wide")

# BRAND COLORS
ACCENT_BLUE = "#3B82F6"
ACCENT_LIME = "#A3E635"
GLASS_BG = "rgba(255, 255, 255, 0.03)"
GLASS_BORDER = "rgba(255, 255, 255, 0.1)"

# 2. UI STYLING
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;800&display=swap');
    html, body, [data-testid="stAppViewContainer"] {{
        background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617);
        font-family: 'Inter', sans-serif;
        color: #f8fafc;
    }}
    /* Glass Cards */
    div[data-testid="stMetric"], .glass-pane {{
        background: {GLASS_BG} !important;
        backdrop-filter: blur(12px);
        border: 1px solid {GLASS_BORDER} !important;
        border-radius: 24px !important;
        padding: 25px !important;
    }}
    /* Hero Title */
    .hero-text {{
        font-size: 50px; font-weight: 800; letter-spacing: -2px;
        background: linear-gradient(to right, #ffffff, #94a3b8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    /* Sidebar */
    section[data-testid="stSidebar"] {{ background-color: rgba(15, 23, 42, 0.8) !important; }}
    </style>
    """, unsafe_allow_html=True)

# 3. LOGIC INIT
g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))
if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# --- NAVIGATION ---
if os.path.exists("logo.png"): st.image("logo.png", width=140)

if st.session_state.m is None:
    st.markdown("<h1 class='hero-text'>Precision intelligence.</h1>", unsafe_allow_html=True)
    up = st.file_uploader("Initialize System", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = process_business_data(raw)
        st.session_state.m = m
        st.rerun()
else:
    m = st.session_state.m
    
    # KPI ROW
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Revenue", f"{m['total_revenue']:,.0f} SAR")
    k2.metric("Profit", f"{m['total_profit']:,.0f} SAR")
    k3.metric("Margin", f"{m['margin_pct']}%")
    k4.metric("Units", f"{m['total_units']:,}")

    st.divider()

    # --- THE INTERACTIVE GRID ---
    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        st.markdown("### 📈 Growth Trend")
        if m.get('trend_data'):
            tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
            fig = px.line(tdf, x='Date', y='Sales')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(l=0,r=0,t=0,b=0))
            fig.update_traces(line_color=ACCENT_BLUE, line_width=4)
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        # THE VISIBLE CHATBOT PANE
        st.markdown("### 💬 TrueMetrics AI")
        st.markdown('<div class="glass-pane">', unsafe_allow_html=True)
        
        # Chat History Container
        chat_container = st.container(height=300)
        with chat_container:
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]): 
                    st.markdown(f'<span style="color:white">{msg["content"]}</span>', unsafe_allow_html=True)
        
        # Input for Chat
        if p := st.chat_input("Analyze your data..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

    if st.sidebar.button("System Reset"):
        st.session_state.m = None
        st.session_state.chat = []
        st.rerun()
