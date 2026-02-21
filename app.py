import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import Truemetrics as tm

# 1. SETUP & LAYOUT
st.set_page_config(page_title="TrueMetrics | Ultra BI", page_icon="🎯", layout="wide")
BLUE, LIME, DARK, PANEL = "#3B82F6", "#A3E635", "#020617", "rgba(255, 255, 255, 0.03)"

# 2. ENGAGING CSS (New Fonts & Densities)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&family=Inter:wght@400;600&display=swap');
    
    .stApp {{
        background: radial-gradient(circle at 15% 50%, rgba(59,130,246,0.1) 0%, transparent 40%),
                    radial-gradient(circle at 85% 30%, rgba(163,230,53,0.08) 0%, transparent 40%), {DARK};
        color: #f8fafc; font-family: 'Inter', sans-serif;
    }}
    
    h1, h2, h3, h4 {{ font-family: 'Outfit', sans-serif !important; font-weight: 700 !important; }}
    
    /* Bigger, Bolder Metric Cards */
    div[data-testid="stMetric"] {{
        background: {PANEL} !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 24px !important;
        padding: 25px 20px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }}
    div[data-testid="stMetricValue"] {{ font-family: 'Outfit', sans-serif !important; font-size: 32px !important; font-weight: 700 !important; color: #fff !important; }}
    div[data-testid="stMetricLabel"] {{ font-size: 14px !important; color: #94a3b8 !important; letter-spacing: 1px; text-transform: uppercase; }}

    .glass-panel {{
        background: {PANEL};
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 24px; padding: 25px; margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }}
    .hero-title {{ font-size: 72px; font-weight: 900; letter-spacing: -2px; line-height: 1; margin: 0; background: linear-gradient(to right, #fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .sub-hero {{ color: {BLUE}; font-family: 'Inter'; font-weight: 600; letter-spacing: 3px; font-size: 14px; text-transform: uppercase; margin-bottom: 40px; }}
    </style>
    """, unsafe_allow_html=True)

# 3. ENGINE INIT
g_client, m_client = tm.configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))
if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# --- APP FLOW ---
if st.session_state.m is None:
    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-title'>TrueMetrics.</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-hero'>Precision Intelligence Dashboard</p>", unsafe_allow_html=True)
    up = st.file_uploader("Upload CSV/XLSX Dataset", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = tm.process_business_data(raw)
        if "error" in m: st.error(m["error"])
        else:
            st.session_state.m = m
            st.rerun()
else:
    m = st.session_state.m

    # 1. TOP KPI ROW (Big & Engaging)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Revenue", f"{m['total_revenue']:,.0f} SAR")
    k2.metric("📈 Net Profit", f"{m['total_profit']:,.0f} SAR")
    k3.metric("🎯 Profit Margin", f"{m['margin_pct']}%")
    k4.metric("🔮 3-Month Forecast", f"{m['forecast']:,.0f} SAR")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 2. MAIN VISUALS (Row 2)
    c_trend, c_chat = st.columns([2.5, 1.2])

    with c_trend:
        st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
        st.markdown(f"<h4><span style='color:{BLUE};'>●</span> Revenue Trajectory</h4>", unsafe_allow_html=True)
        if m['trend_data']:
            tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
            fig = px.area(tdf, x='Date', y='Sales')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=350, margin=dict(l=0,r=0,t=0,b=0))
            fig.update_traces(line_color=BLUE, fillcolor='rgba(59, 130, 246, 0.1)', line_width=4)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_chat:
        st.markdown("<div class='glass-panel' style='height: 450px;'>", unsafe_allow_html=True)
        st.markdown(f"<h4>🤖 Data Expert</h4>", unsafe_allow_html=True)
        chat_box = st.container(height=280)
        with chat_box:
            for msg in st.session_state.chat[-5:]:
                with st.chat_message(msg["role"]): st.write(msg["content"])
        if p := st.chat_input("Ask about your data..."):
            st.session_state.chat.append({"role": "user", "content": p})
            st.session_state.chat.append({"role": "assistant", "content": tm.get_ai_response(m_client, m, p)})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. DEEP INSIGHTS (Row 3)
    c_donut, c_top, c_bot = st.columns([1.2, 1, 1])

    with c_donut:
        st.markdown("<div class='glass-panel' style='height: 380px;'>", unsafe_allow_html=True)
        st.markdown(f"<h4>📍 Market Share</h4>", unsafe_allow_html=True)
        if m['city_dist']:
            # Highly engaging Hollow Donut Chart
            fig_pie = go.Figure(data=[go.Pie(labels=list(m['city_dist'].keys()), values=list(m['city_dist'].values()), hole=.6)])
            fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(l=0,r=0,t=20,b=0), height=250, showlegend=False)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', marker=dict(colors=['#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#EFF6FF']))
            st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_top:
        st.markdown("<div class='glass-panel' style='height: 380px;'>", unsafe_allow_html=True)
        st.markdown(f"<h4><span style='color:{LIME};'>▲</span> Peak Margins</h4>", unsafe_allow_html=True)
        st.write("Top performing segments in your dataset:")
        st.markdown("<br>", unsafe_allow_html=True)
        for i in m['top_margins']: 
            st.markdown(f"<div style='background:rgba(163,230,53,0.1); padding:12px; border-radius:10px; margin-bottom:8px; border-left:4px solid {LIME};'><b>{i}</b></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_bot:
        st.markdown("<div class='glass-panel' style='height: 380px;'>", unsafe_allow_html=True)
        st.markdown(f"<h4><span style='color:#ef4444;'>▼</span> Margin Risks</h4>", unsafe_allow_html=True)
        st.write("Segments requiring immediate optimization:")
        st.markdown("<br>", unsafe_allow_html=True)
        for i in m['bot_margins']: 
            st.markdown(f"<div style='background:rgba(239,68,68,0.1); padding:12px; border-radius:10px; margin-bottom:8px; border-left:4px solid #ef4444;'><b>{i}</b></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Reset
    if st.sidebar.button("Clear Dashboard"):
        st.session_state.m = None
        st.session_state.chat = []
        st.rerun()
