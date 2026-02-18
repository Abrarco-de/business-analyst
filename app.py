import streamlit as st
import pandas as pd
import plotly.express as px
from business_ai_mvp import *

# 1. Config & Styling
st.set_page_config(page_title="Visionary SME Analyst", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0F172A !important; color: #F8FAFC !important; }
    div[data-testid="metric-container"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        padding: 20px !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
    }
    div[data-testid="stMetricValue"] { color: #38BDF8 !important; font-weight: 800 !important; }
    h1, h2, h3, p { color: #F1F5F9 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Sidebar & Engines
with st.sidebar:
    st.markdown("<h2 style='color:#38BDF8;'>💎 Settings</h2>", unsafe_allow_html=True)
    groq_client = configure_engines(st.secrets["GEMINI_API_KEY"], st.secrets["GROQ_API_KEY"])
    if st.button("🗑️ Reset All", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# 3. Main Dashboard
st.markdown("<h1 style='text-align: center; color: #38BDF8;'>Visionary SME Analyst</h1>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["csv", "xlsx"])

if uploaded_file:
    try:
        df_raw = pd.read_csv(uploaded_file, encoding='latin1') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        with st.status("⚡ Dual-Agent Intelligence Syncing...", expanded=False):
            m, df_final = calculate_precise_metrics(df_raw)
            st.session_state['data_loaded'] = True
            st.session_state['m'] = m
            st.session_state['df_final'] = df_final

        # --- Metrics Display ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("REVENUE", f"{m['rev']:,.0f} SAR")
        m2.metric("PROFIT", f"{m['prof']:,.0f} SAR")
        m3.metric("VAT (15%)", f"{m['vat']:,.0f} SAR")
        m4.metric("LEAD PRODUCT", m['best_seller'][:15])

        st.divider()

        # --- Analytics Grid ---
        col_left, col_right = st.columns([1.2, 0.8])

        with col_left:
            st.subheader("📈 Performance Analysis")
            fig = px.bar(df_final.groupby(m['p_col'])['_rev'].sum().reset_index().head(10), 
                         x=m['p_col'], y='_rev', color='_rev', template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("💬 Data Concierge")
            chat_container = st.container(height=400, border=True)
            
            if "messages" not in st.session_state: st.session_state.messages = []
            
            with chat_container:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]): st.markdown(msg["content"])

            if prompt := st.chat_input("Ask a specific data question..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with chat_container:
                    with st.chat_message("user"): st.markdown(prompt)
                
                with chat_container:
                    with st.chat_message("assistant"):
                        with st.spinner("🕵️ Gemini researching... 🧠 Groq analyzing..."):
                            answer = get_intelligent_answer(groq_client, df_final, prompt, m)
                            st.markdown(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("👋 Upload a CSV or Excel file to begin your premium analysis.")
