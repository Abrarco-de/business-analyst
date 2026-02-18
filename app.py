import streamlit as st
import pandas as pd
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

# 1. UI Configuration
st.set_page_config(page_title="Visionary SME AI", layout="wide")

# 2. Session State Initialization
if "m" not in st.session_state: 
    st.session_state.m = None
if "chat_history" not in st.session_state: 
    st.session_state.chat_history = []

# 3. Engine Setup (Always run)
g_key = st.secrets.get("GROQ_API_KEY")
m_key = st.secrets.get("MISTRAL_API_KEY")
g_client, m_client = configure_dual_engines(g_key, m_key)

# 4. Main Page Title
st.title("📊 Visionary SME Dashboard")

# 5. UPLOAD LOGIC (Main Page if no data, Sidebar if data exists)
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

# 6. DATA PROCESSING
if uploaded_file:
    try:
        df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
        with st.spinner("Calculating Advanced Metrics..."):
            m, _ = process_business_data(g_client, df_raw)
            st.session_state.m = m
            # We don't rerun here to allow the UI to catch up
    except Exception as e:
        st.error(f"File Error: {e}")

# 7. DASHBOARD RENDERING
if st.session_state.m:
    m = st.session_state.m
    
    # ROW 1: CORE FINANCIALS
    st.subheader("💰 Financial Overview")
    r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns(5)
    r1c1.metric("Total Revenue", f"{m.get('total_revenue', 0):,}")
    r1c2.metric("Total Profit", f"{m.get('total_profit', 0):,}")
    r1c3.metric("Gross Margin", f"{m.get('gross_margin_pct', 0)}%")
    r1c4.metric("VAT Due (15%)", f"{m.get('vat_due', 0):,}")
    r1c5.metric("Avg Trans.", f"{m.get('avg_transaction', 0):,}")

    st.divider()

    # ROW 2: OPERATIONS
    st.subheader("📦 Operations & Volume")
    r2c1, r2c2, r2c3 = st.columns(3)
    r2c1.metric("Units Sold", f"{m.get('total_units', 0):,}")
    r2c2.metric("Rev Per Unit", f"{m.get('rev_per_unit', 0):,}")
    top_p = m.get('top_prof_prods', ['N/A'])[0]
    r2c3.info(f"🏆 **Top Profit Maker:**\n{top_p}")

    # ROW 3: PRODUCT INSIGHT TABLES
    st.divider()
    t1, t2 = st.columns(2)
    with t1:
        st.markdown("### ⚠️ Attention Needed")
        st.error(f"**Loss Making:** {', '.join(m.get('loss_making', [])) if m.get('loss_making') else 'None'}")
        st.warning(f"**High Vol/Low Margin:** {', '.join(m.get('high_vol_low_margin', [])) if m.get('high_vol_low_margin') else 'None'}")
    with t2:
        st.markdown("### 📈 Top Performers")
        st.success(f"**Top Revenue:** {', '.join(m.get('top_rev_prods', []))}")
        st.info(f"**Low Margin items:** {', '.join(m.get('low_margin', [])) if m.get('low_margin') else 'None'}")

    # 8. FLOATING CHATBOT (Popover)
    # Positioning style
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px; z-index: 1000;}</style>""", unsafe_allow_html=True)
    
    with st.popover("💬 Chat with AI"):
        st.write("### AI Business Consultant")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Ask about your strategy..."):
            st.session_state.chat_history.append({"role": "user", "content": p})
            with st.spinner("AI is analyzing..."):
                ans = get_ai_response(m_client, st.session_state.m, p)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
            st.rerun()
else:
    # If no data is uploaded, show a placeholder image or guide
    st.write("---")
    st.warning("Please upload a CSV or Excel file to populate the dashboard metrics.")
