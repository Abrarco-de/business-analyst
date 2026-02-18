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

# 3. Sidebar Setup
with st.sidebar:
    st.title("🔑 AI Control Panel")
    # Ensure keys are in .streamlit/secrets.toml
    g_key = st.secrets.get("GROQ_API_KEY")
    m_key = st.secrets.get("MISTRAL_API_KEY")
    g_client, m_client = configure_dual_engines(g_key, m_key)
    
    uploaded_file = st.file_uploader("Upload Business Data", type=["csv", "xlsx"])
    
    if st.button("🗑️ Reset Everything"):
        st.session_state.m = None
        st.session_state.chat_history = []
        st.rerun()

# 4. Main Title
st.title("📊 Visionary SME Dashboard")

# 5. DATA PROCESSING LOGIC
if uploaded_file:
    # Only process if not already in session state
    if st.session_state.m is None:
        with st.spinner("Analyzing your data..."):
            df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
            m, _ = process_business_data(g_client, df_raw)
            st.session_state.m = m

# 6. UI RENDERING (The Conditional Part)
if st.session_state.m:
    m = st.session_state.m
    
    # Row 1: Core Financials
    r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns(5)
    r1c1.metric("Total Revenue", f"{m['total_revenue']:,} SAR")
    r1c2.metric("Total Profit", f"{m['total_profit']:,} SAR")
    r1c3.metric("Gross Margin", f"{m['gross_margin_pct']}%")
    r1c4.metric("VAT Due (15%)", f"{m['vat_due']:,} SAR")
    r1c5.metric("Avg Trans.", f"{m['avg_transaction']:,} SAR")

    st.divider()

    # Row 2: Performance & Units
    r2c1, r2c2, r2c3 = st.columns(3)
    r2c1.metric("Total Units Sold", f"{m['total_units']:,}")
    r2c2.metric("Rev Per Unit", f"{m['rev_per_unit']:,} SAR")
    r2c3.info(f"🏆 **Top Profit Maker:** {m['top_prof_prods'][0] if m['top_prof_prods'] else 'N/A'}")

    # Row 3: Detail Tables
    t1, t2 = st.columns(2)
    with t1:
        st.subheader("⚠️ Action Required")
        st.error(f"**Loss Making:** {', '.join(m['loss_making']) if m['loss_making'] else 'None'}")
        st.warning(f"**High Vol/Low Margin:** {', '.join(m['high_vol_low_margin']) if m['high_vol_low_margin'] else 'None'}")
    with t2:
        st.subheader("📈 Top Performers")
        st.success(f"**Top Revenue:** {', '.join(m['top_rev_prods'])}")
        st.info(f"**Low Margin items:** {', '.join(m['low_margin']) if m['low_margin'] else 'None'}")

    # --- 7. FLOATING CHATBOT ---
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px;}</style>""", unsafe_allow_html=True)
    with st.popover("💬 Ask AI Strategy"):
        st.write("### Business Consultant")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Ask: How to improve margin?"):
            st.session_state.chat_history.append({"role": "user", "content": p})
            with st.spinner("Mistral thinking..."):
                ans = get_ai_response(m_client, st.session_state.m, p)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
            st.rerun()

else:
    # This shows when NO data is uploaded
    st.info("👋 Welcome! Please upload your daily sales or finance CSV/Excel file in the sidebar to generate your AI-powered dashboard.")
    st.image("https://via.placeholder.com/800x400.png?text=Awaiting+Data+Upload...", use_container_width=True)
