import streamlit as st
import pandas as pd
import plotly.express as px
from sahm_engine import configure_dual_engines, process_business_data, get_ai_response

# 1. Page Config & Professional Styling
st.set_page_config(page_title="Sahm BI | Business Insights", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. Sidebar Branding
with st.sidebar:
    st.title("🏹 Sahm BI")
    st.caption("Advanced SME Analytics")
    st.divider()
    # Add a logo link here if you have one:
    # st.image("logo.png", width=150)
    
    if st.button("🔄 Reset Environment", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# 3. Initialization
if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))

# 4. Main UI Logic
if st.session_state.m is None:
    st.subheader("Welcome to Sahm BI")
    up = st.file_uploader("Upload Business Records (CSV/Excel)", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        with st.spinner("Analyzing performance..."):
            m = process_business_data(raw)
            if "error" in m: st.error(m["error"])
            else:
                st.session_state.m = m
                st.rerun()
else:
    m = st.session_state.m
    
    # Professional Header
    st.title("📈 Executive Overview")
    
    # KPI Row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"{m['total_revenue']:,.0f} SAR")
    c2.metric("Net Profit", f"{m['total_profit']:,.0f} SAR")
    c3.metric("VAT Liability (15%)", f"{m['vat_due']:,.0f} SAR", delta_color="inverse")
    c4.metric("Profit Margin", f"{m['margin']}%")

    st.divider()

    # Insight Row
    col_left, col_right = st.columns([2, 1])
    
    with col_right:
        st.subheader("💬 Sahm AI Consultant")
        container = st.container(height=350)
        for msg in st.session_state.chat:
            with container.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Ask about VAT, Cities, or Sales..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()

    with col_left:
        st.subheader("📊 Strategic Performance")
        # Quick visual of Category Performance
        prof = m.get('data_profile', {})
        if prof.get('top_cats'):
            tdf = pd.DataFrame(prof['top_cats'].items(), columns=['Category', 'Sales'])
            fig = px.bar(tdf, x='Category', y='Sales', color='Sales', 
                         color_continuous_scale='Blues', title="Top Performing Categories")
            st.plotly_chart(fig, use_container_width=True)
