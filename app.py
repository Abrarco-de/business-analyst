import streamlit as st
import pandas as pd
import plotly.express as px
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

st.set_page_config(page_title="Visionary SME AI", layout="wide")

if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))

st.title("📊 SME Enterprise Intelligence")

try:
    if st.session_state.m is None:
        up = st.file_uploader("Upload Business Data", type=["csv", "xlsx"])
        if up:
            raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
            m, _ = process_business_data(g_client, raw)
            if "error" in m: 
                st.error(m["error"])
            else:
                st.session_state.m = m
                st.rerun()
    else:
        m = st.session_state.m
        meta = m.get('meta', {})
        
        if st.sidebar.button("🗑️ Reset"):
            st.session_state.m = None
            st.rerun()

        # KPI ROW
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Revenue", f"{m.get('total_revenue', 0):,.0f} SAR")
        k2.metric(f"Profit ({meta.get('profit_method', 'Est')})", f"{m.get('total_profit', 0):,.0f} SAR")
        k3.metric("Gross Margin", f"{m.get('margin_pct', 0)}%")

        st.divider()

        # MARGINS
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("📉 Least Margin")
            for item in m.get('bot_margin_list', []): st.error(item)
        with col_b:
            st.subheader("📈 Top Margin")
            for item in m.get('top_margin_list', []): st.success(item)

        # TREND
        if m.get('trend_data'):
            st.divider()
            tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Revenue'])
            st.plotly_chart(px.line(tdf, x='Date', y='Revenue', title="Revenue Performance"))

        # CHAT
        st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px;}</style>""", unsafe_allow_html=True)
        with st.popover("💬 AI Strategist"):
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]): st.write(msg["content"])
            if p := st.chat_input("Ask..."):
                st.session_state.chat.append({"role": "user", "content": p})
                ans = get_ai_response(m_client, m, p)
                st.session_state.chat.append({"role": "assistant", "content": ans})
                st.rerun()

except Exception as e:
    st.error(f"🛑 Critical UI Crash: {str(e)}")
    st.info("Try clicking 'Reset' or refreshing the page.")
