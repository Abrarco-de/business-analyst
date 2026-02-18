import streamlit as st
import pandas as pd
import plotly.express as px  # Professional charts
from business_ai_mvp import configure_engines, calculate_precise_metrics, groq_get_insights

# 1. Force Page Config
st.set_page_config(page_title="Visionary Analyst", page_icon="💎", layout="wide")

# 2. Enhanced CSS (Fixes the "White" contrast issue)
st.markdown("""
    <style>
    /* Force a professional light-gray background */
    .stApp { background-color: #F3F4F6; }
    
    /* Metrics Card Styling */
    [data-testid="metric-container"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        padding: 25px !important;
        border-radius: 15px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
        color: #111827 !important;
    }
    
    /* Title and Header Colors */
    h1, h2, h3 { color: #1E3A8A !important; font-family: 'Inter', sans-serif; }
    
    /* Sidebar styling */
    .stSidebar { background-color: #111827 !important; color: white !important; }
    
    /* Custom button styling */
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #2563EB; border: none; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar (Persistent Controls)
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
    GROQ_KEY = st.secrets.get("GROQ_API_KEY")
    groq_client = configure_engines(GEMINI_KEY, GROQ_KEY)
    
    st.divider()
    if st.button("🔄 Reset Analysis"):
        st.session_state.clear()
        st.rerun()

# 4. Header Section
st.markdown("# 💎 Visionary SME Analyst")
st.markdown("#### Enterprise Data Intelligence | ZATCA Compliant")

uploaded_file = st.file_uploader("📂 Upload Business Sales Data", type=["csv", "xlsx"])

if uploaded_file:
    try:
        df_input = pd.read_csv(uploaded_file, encoding='latin1') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        with st.status("🔮 AI Engines Working...", expanded=False) as status:
            m, df_final = calculate_precise_metrics(df_input)
            st.session_state['data'] = (m, df_final)
            status.update(label="✅ Ready for Insight", state="complete")

        # --- Metrics Row ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Revenue", f"{m['rev']:,.2f} SAR")
        m2.metric("Net Profit", f"{m['prof']:,.2f} SAR")
        m3.metric("ZATCA VAT (15%)", f"{m['vat']:,.2f} SAR")
        m4.metric("Performance Leader", m['best_seller'][:12])

        st.divider()

        # --- Dashboard Grid ---
        col_left, col_right = st.columns([1.2, 0.8])

        with col_left:
            st.subheader("📊 Revenue by Category")
            # Interactive Plotly Chart
            fig = px.bar(
                df_final.groupby(m['p_col'])['_rev'].sum().reset_index(),
                x=m['p_col'], y='_rev',
                color='_rev',
                labels={'_rev': 'Revenue (SAR)', m['p_col']: 'Product'},
                template="plotly_white",
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig, use_container_width=True)

            if st.button("✨ Generate Advanced Strategy"):
                with st.spinner("Analyzing with Llama 3..."):
                    insights = groq_get_insights(groq_client, m)
                    st.info(insights)

        with col_right:
            st.subheader("💬 Data Chat")
            chat_box = st.container(height=400, border=True)
            
            if "messages" not in st.session_state: st.session_state.messages = []
            
            with chat_box:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]): st.markdown(msg["content"])

            if prompt := st.chat_input("Ask about margins, tax, or trends..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with chat_box:
                    with st.chat_message("user"): st.markdown(prompt)
                
                # Context Injection
                context = f"Revenue {m['rev']}, Profit {m['prof']}, Top Item {m['best_seller']}. Question: {prompt}"
                
                with chat_box:
                    with st.chat_message("assistant"):
                        res = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": context}]
                        )
                        answer = res.choices[0].message.content
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        st.error(f"⚠️ Data mismatch: {e}")

else:
    st.write("---")
    st.image("https://img.freepik.com/free-vector/data-analysis-concept-illustration_114360-1611.jpg", width=400)
    st.info("👋 Welcome! Please upload your sales data in the sidebar or main window to begin your AI-powered analysis.")
    
