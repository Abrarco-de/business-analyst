import streamlit as st
import pandas as pd
import plotly.express as px # Requires: pip install plotly

# Import the engine
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

# 1. PAGE SETUP
st.set_page_config(page_title="Visionary SME AI", layout="wide", page_icon="📊")

# Initialize Session State
if "metrics" not in st.session_state: st.session_state.metrics = None
if "df_processed" not in st.session_state: st.session_state.df_processed = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# 2. SIDEBAR CONFIG
with st.sidebar:
    st.title("⚙️ Data Settings")
    g_key = st.secrets.get("GROQ_API_KEY")
    m_key = st.secrets.get("MISTRAL_API_KEY")
    g_client, m_client = configure_dual_engines(g_key, m_key)
    
    uploaded_file = st.file_uploader("Upload Finance/Sales Data", type=["csv", "xlsx"])
    
    if st.button("🔄 Reset Dashboard"):
        st.session_state.metrics = None
        st.session_state.df_processed = None
        st.session_state.chat_history = []
        st.rerun()

# 3. DATA PROCESSING ORCHESTRATOR
if uploaded_file and st.session_state.metrics is None:
    try:
        # Load Raw
        if uploaded_file.name.endswith('csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
            
        with st.spinner("🔍 detecting schema & calculating metrics..."):
            # Call the Engine
            metrics, df_proc = process_business_data(g_client, df_raw)
            
            # Error Check
            if metrics.get("error"):
                st.error(f"Data Processing Failed: {metrics['error']}")
            else:
                st.session_state.metrics = metrics
                st.session_state.df_processed = df_proc
                st.rerun() # Refresh to show dashboard
                
    except Exception as e:
        st.error(f"Critical Error: {str(e)}")

# 4. MAIN DASHBOARD RENDER
st.title("📊 Enterprise Business Intelligence")

if st.session_state.metrics:
    m = st.session_state.metrics
    meta = m['meta']

    # --- ROW 1: KPI CARDS ---
    st.markdown("### 🏦 Financial Performance")
    k1, k2, k3, k4, k5 = st.columns(5)
    
    k1.metric("Total Revenue", f"{m['total_revenue']:,.0f} SAR")
    
    # Conditional Formatting for Profit (Warn if Estimated)
    prof_label = "Total Profit"
    if not meta['has_real_profit']: prof_label += " (Est. 20%)"
    k2.metric(prof_label, f"{m['total_profit']:,.0f} SAR")
    
    k3.metric("Gross Margin", f"{m['gross_margin_pct']}%")
    k4.metric("Avg Order Value", f"{m['avg_order_value']:,.1f} SAR")
    
    # Handle Optional Quantity
    if m['total_units']:
        k5.metric("Total Units", f"{m['total_units']:,}")
    else:
        k5.metric("Total Units", "N/A", help="No Quantity column found")

    st.divider()

    # --- ROW 2: DEEP INSIGHTS ---
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("📉 Margin Analysis")
        st.caption("Lowest Margin Products (Potential Loss Makers)")
        # Parse the string we built in the engine for display
        items = m['lowest_margin_str'].split(", ")
        for item in items:
            st.error(item)
            
    with c2:
        st.subheader("📈 Revenue Drivers")
        st.caption("Top Products by Sales Volume")
        for item in m['top_revenue_items']:
            st.success(item)

    # --- ROW 3: TREND ANALYSIS (Conditional) ---
    if meta['has_date'] and m['trend_data']:
        st.divider()
        st.subheader("📅 Sales Trend Over Time")
        trend_df = pd.DataFrame(list(m['trend_data'].items()), columns=['Date', 'Revenue'])
        fig = px.line(trend_df, x='Date', y='Revenue', title="Revenue Timeline")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 Note: No Date column detected, so Trend Analysis is hidden.")

    # --- 5. FLOATING AI CHAT ---
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px; z-index:999;}</style>""", unsafe_allow_html=True)
    
    with st.popover("🤖 Consultant AI"):
        st.caption("Ask specific questions about your data context.")
        
        # Chat History
        for msg in st.session_state.chat_history:
            role = "user" if msg["role"] == "user" else "assistant"
            with st.chat_message(role): st.write(msg["content"])
            
        # Input
        if query := st.chat_input("Ex: Why is margin so low?"):
            st.session_state.chat_history.append({"role": "user", "content": query})
            with st.chat_message("user"): st.write(query)
            
            with st.spinner("Analyzing metrics..."):
                ans = get_ai_response(m_client, m, query)
                
            with st.chat_message("assistant"): st.write(ans)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})

elif not uploaded_file:
    # Empty State
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h2>👋 Welcome to Visionary SME AI</h2>
        <p>Please upload your <b>Sales or Finance CSV/Excel</b> from the sidebar.</p>
        <p style='color: gray; font-size: 0.9em;'>Supports: Supermart, POS Reports, Standard Ledgers</p>
    </div>
    """, unsafe_allow_html=True)
