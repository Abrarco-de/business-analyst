import streamlit as st
import pandas as pd
import plotly.express as px
import os
from Truemetrics import configure_dual_engines, process_business_data, get_ai_response

# 1. High-End Page Config
st.set_page_config(page_title="TrueMetrics | Intelligence", page_icon="🎯", layout="wide")

# BRAND COLOR PALETTE
ACCENT_BLUE = "#3B82F6"
ACCENT_LIME = "#A3E635"
GLASS_BG = "rgba(255, 255, 255, 0.03)"
GLASS_BORDER = "rgba(255, 255, 255, 0.1)"

# 2. THE TPCAP STYLING (The Secret Sauce)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"] {{
        background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617);
        font-family: 'Inter', sans-serif;
        color: #f8fafc;
    }}

    /* The Glassmorphism Effect */
    div[data-testid="stMetric"] {{
        background: {GLASS_BG} !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid {GLASS_BORDER} !important;
        border-radius: 24px !important;
        padding: 30px !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}

    div[data-testid="stMetric"]:hover {{
        transform: translateY(-10px);
        border-color: {ACCENT_BLUE} !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4), 0 0 20px rgba(59, 130, 246, 0.2);
    }}

    /* Custom Header Styles */
    .hero-text {{
        font-size: 64px;
        font-weight: 800;
        letter-spacing: -2px;
        background: linear-gradient(to right, #ffffff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }}

    /* Data Visualization Container */
    .viz-card {{
        background: {GLASS_BG};
        border-radius: 32px;
        padding: 20px;
        border: 1px solid {GLASS_BORDER};
    }}

    /* Hide default Streamlit clutter */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# 3. APP INITIALIZATION
g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))

if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# --- TOP NAVIGATION ---
col_logo, col_space = st.columns([1, 4])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=140)
    else:
        st.markdown(f"<h1 style='color:{ACCENT_LIME}'>🎯</h1>", unsafe_allow_html=True)

# --- HERO SECTION ---
if st.session_state.m is None:
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-text'>Precision intelligence<br>for the next era.</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#64748b; font-size:20px;'>Upload your dataset to initialize TrueMetrics AI.</p>", unsafe_allow_html=True)
    
    up = st.file_uploader("", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = process_business_data(raw)
        if "error" in m: st.error(m["error"])
        else:
            st.session_state.m = m
            st.rerun()
else:
    m = st.session_state.m
    
    # Header for Active Dashboard
    st.markdown("<h2 style='font-weight:700; margin-bottom:30px;'>Live Insight Matrix</h2>", unsafe_allow_html=True)

    # --- GLASS KPI GRID ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Revenue", f"{m['total_revenue']:,.0f} SAR")
    k2.metric("Net Profit", f"{m['total_profit']:,.0f} SAR")
    k3.metric("Margin", f"{m['margin_pct']}%")
    k4.metric("Units", f"{m['total_units']:,}")

    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

    # --- INTERACTIVE CONTENT ---
    col_viz, col_alerts = st.columns([2, 1])

    with col_viz:
        if m.get('trend_data'):
            tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
            fig = px.line(tdf, x='Date', y='Sales', template="plotly_dark")
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                margin=dict(l=0, r=0, t=0, b=0),
                height=350
            )
            fig.update_traces(line_color=ACCENT_BLUE, line_width=4, fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)')
            st.markdown("<div class='viz-card'>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col_alerts:
        st.markdown("<div class='viz-card' style='height:350px; overflow-y:auto;'>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{ACCENT_LIME}; font-weight:bold;'>Top Performers</p>", unsafe_allow_html=True)
        for i in m['top_margin_list']:
            st.markdown(f"<p style='font-size:14px; margin-bottom:5px; padding-left:10px; border-left:2px solid {ACCENT_LIME}'>{i}</p>", unsafe_allow_html=True)
        
        st.divider()
        
        st.markdown(f"<p style='color:#ef4444; font-weight:bold;'>Efficiency Gaps</p>", unsafe_allow_html=True)
        for i in m['bot_margin_list']:
            st.markdown(f"<p style='font-size:14px; margin-bottom:5px; padding-left:10px; border-left:2px solid #ef4444'>{i}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- THE FLOATING AI BUTTON ---
    st.markdown("""<style>
        .stPopover {position: fixed; bottom: 30px; right: 30px;}
        .stPopover button {
            background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
            border-radius: 50% !important;
            width: 70px !important; height: 70px !important;
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.4) !important;
            border: none !important;
        }
    </style>""", unsafe_allow_html=True)

    with st.popover("💬"):
        st.markdown("<h3 style='margin-top:0;'>TrueMetrics Intelligence</h3>", unsafe_allow_html=True)
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Speak with the engine..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()

    if st.sidebar.button("System Reset"):
        st.session_state.m = None
        st.rerun()
