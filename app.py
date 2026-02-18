import streamlit as st
import pandas as pd
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

st.set_page_config(page_title="Visionary SME AI", layout="wide")

if "m" not in st.session_state: st.session_state.m = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []

g_key, m_key = st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY")
g_client, m_client = configure_dual_engines(g_key, m_key)

st.title("📊 Visionary SME Dashboard")

# MAIN UPLOADER
if st.session_state.m is None:
    st.info("👋 Welcome! Please upload your business data to begin.")
    uploaded_file = st.file_uploader("Upload Daily Sales/Finance (CSV or Excel)", type=["csv", "xlsx"])
else:
    with st.sidebar:
        st.header("⚙️ Controls")
        uploaded_file = st.file_uploader("Upload New Data", type=["csv", "xlsx"])
        if st.button("🗑️ Reset Dashboard"):
            st.session_state.m = None
            st.session_state.chat_history = []
            st.rerun()

if uploaded_file:
    try:
        df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
        st.session_state.m, _ = process_business_data(g_client, df_raw)
    except Exception as e: st.error(f"File Error: {e}")

# DASHBOARD DISPLAY
if st.session_state.m:
    m = st.session_state.m
    
    # FINANCIAL CARDS
    st.subheader("💰 Financial Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Revenue", f"{m['total_revenue']:,} SAR")
    c2.metric("Total Profit", f"{m['total_profit']:,} SAR")
    c3.metric("Gross Margin", f"{m['gross_margin_pct']}%")
    c4.metric("VAT (15%)", f"{m['vat_due']:,} SAR")
    c5.metric("Weakest Margin Item", m.get('least_margin_name', 'N/A').split('(')[0])

    st.divider()

    # OPERATIONAL CARDS
    st.subheader("📦 Operations & Volume")
    o1, o2, o3 = st.columns(3)
    o1.metric("Units Sold", f"{m['total_units']:,}")
    o2.metric("Rev Per Unit", f"{m['rev_per_unit']:,} SAR")
    top_p = m['top_prof_prods'][0] if m['top_prof_prods'] else 'N/A'
    o3.info(f"🏆 **Top Profit Maker:**\n{top_p}")

    # TABLES
    st.divider()
    t1, t2 = st.columns(2)
    with t1:
        st.markdown("### ⚠️ Action Required")
        st.error(f"**Loss Making:** {', '.join(m['loss_making']) if m['loss_making'] else 'None'}")
        st.warning(f"**High Vol/Low Margin:** {', '.join(m['high_vol_low_margin']) if m['high_vol_low_margin'] else 'None'}")
    with t2:
        st.markdown("### 📈 Top Performers")
        st.success(f"**Top Revenue:** {', '.join(m['top_rev_prods'])}")
        st.info(f"**Low Margin items:** {', '.join(m['low_margin']) if m['low_margin'] else 'None'}")

    # CHAT POPOVER
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px; z-index: 1000;}</style>""", unsafe_allow_html=True)
    with st.popover("💬 Chat with AI"):
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        if p := st.chat_input("Analyze these results..."):
            st.session_state.chat_history.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, st.session_state.m, p)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
            st.rerun()


