import streamlit as st
import pandas as pd
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

st.set_page_config(page_title="Visionary SME AI", layout="wide")

# 1. Initialize Session
if "m" not in st.session_state: st.session_state.m = {}
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# 2. Sidebar Keys
with st.sidebar:
    st.header("🔑 Setup")
    g_client, m_client = configure_dual_engines(st.secrets["GROQ_API_KEY"], st.secrets["MISTRAL_API_KEY"])
    uploaded_file = st.file_uploader("Upload Dataset", type=["csv", "xlsx"])

# 3. Data Processing
if uploaded_file:
    df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
    st.session_state.m, _ = process_business_data(g_client, df_raw)

# 4. Main Dashboard UI
st.title("📊 Business Intelligence Home")
m = st.session_state.m

if m:
    # Row 1: Core Financials
    r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns(5)
    r1c1.metric("Total Revenue", f"{m['total_revenue']:,} SAR")
    r1c2.metric("Total Profit", f"{m['total_profit']:,} SAR")
    r1c3.metric("Gross Margin", f"{m['gross_margin_pct']}%")
    r1c4.metric("VAT Due (15%)", f"{m['vat_due']:,} SAR")
    r1c5.metric("Avg Transaction", f"{m['avg_transaction']:,} SAR")

    # Row 2: Operational Metrics
    st.divider()
    r2c1, r2c2, r2c3 = st.columns(3)
    r2c1.metric("Total Units Sold", f"{m['total_units']:,}")
    r2c2.metric("Revenue Per Unit", f"{m['rev_per_unit']:,} SAR")
    r2c3.write(f"**Top Profit Maker:** {m['top_prof_prods'][0] if m['top_prof_prods'] else 'N/A'}")

    # Row 3: Insights Tables
    t1, t2 = st.columns(2)
    with t1:
        st.subheader("⚠️ Attention Needed")
        st.write("**Loss Making Products:**", m['loss_making'] if m['loss_making'] else "None 🎉")
        st.write("**High Volume / Low Margin:**", m['high_vol_low_margin'] if m['high_vol_low_margin'] else "None")
    with t2:
        st.subheader("🏆 Performance")
        st.write("**Top Revenue Products:**", m['top_rev_prods'])
        st.write("**Low Margin Products:**", m['low_margin'])

# --- 5. FLOATING CHATBOT ICON ---
st.markdown("""<style>.stPopover {position: fixed; bottom: 20px; right: 20px;}</style>""", unsafe_allow_html=True)

with st.popover("💬 Chat with AI Strategist"):
    st.caption("I have access to your dashboard metrics.")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if p := st.chat_input("Ask about your strategy..."):
        st.session_state.chat_history.append({"role": "user", "content": p})
        ans = get_ai_response(m_client, st.session_state.m, p)
        st.session_state.chat_history.append({"role": "assistant", "content": ans})
        st.rerun()
