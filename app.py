import streamlit as st
import pandas as pd
import plotly.express as px
from business_ai_mvp import configure_engines, calculate_precise_metrics, groq_get_insights

# 1. Page Config
st.set_page_config(page_title="Visionary Analyst Pro", page_icon="💎", layout="wide")

# 2. Premium Dark CSS
st.markdown("""
    <style>
    /* Force Deep Midnight Background */
    .stApp {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
    }

    /* Premium Glassmorphism Cards */
    div[data-testid="metric-container"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        padding: 20px !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
    }

    /* Metric Text Colors */
    div[data-testid="stMetricValue"] {
        color: #38BDF8 !important; /* Neon Blue */
        font-weight: 800 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important; /* Slate Gray */
    }

    /* Chat Styling */
    .stChatMessage {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sidebar Darkening */
    section[data-testid="stSidebar"] {
        background-color: #020617 !important;
    }
    
    /* Global Text Force White */
    h1, h2, h3, p, span, label {
        color: #F1F5F9 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar
with st.sidebar:
    st.markdown("<h2 style='color:#38BDF8;'>💎 Visionary Pro</h2>", unsafe_allow_html=True)
    GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
    GROQ_KEY = st.secrets.get("GROQ_API_KEY")
    groq_client = configure_engines(GEMINI_KEY, GROQ_KEY)
    
    if st.button("🗑️ Reset Workspace", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# 4. Main Stage
st.markdown("<h1 style='text-align: center; color: #38BDF8;'>Visionary SME Analyst</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94A3B8;'>Next-Gen Intelligence for Saudi Enterprises</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["csv", "xlsx"])

if uploaded_file:
    try:
        df_input = pd.read_csv(uploaded_file, encoding='latin1') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        with st.status("⚡ Powering AI Engines...", expanded=False) as status:
            m, df_final = calculate_precise_metrics(df_input)
            st.session_state['data'] = (m, df_final)
            status.update(label="✅ System Online", state="complete")

        # --- Dashboard Metrics ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("REVENUE", f"{m['rev']:,.0f} SAR")
        m2.metric("NET PROFIT", f"{m['prof']:,.0f} SAR")
        m3.metric("VAT (15%)", f"{m['vat']:,.0f} SAR")
        m4.metric("TOP SELLER", m['best_seller'][:15])

        st.divider()

        # --- Dual-Pane Layout ---
        col_left, col_right = st.columns([1.2, 0.8])

        with col_left:
            st.markdown("### 📈 Revenue Distribution")
            # Dark Theme Plotly
            fig = px.bar(
                df_final.groupby(m['p_col'])['_rev'].sum().reset_index(),
                x=m['p_col'], y='_rev',
                color='_rev',
                template="plotly_dark", # Forces dark theme on chart
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="#F8FAFC"
            )
            st.plotly_chart(fig, use_container_width=True)

            if st.button("🪄 Generate Executive Insights", use_container_width=True):
                with st.spinner("Llama 3 is analyzing..."):
                    insights = groq_get_insights(groq_client, m)
                    st.markdown(f"<div style='background-color:#1E293B; padding:20px; border-radius:10px; border-left: 5px solid #38BDF8;'>{insights}</div>", unsafe_allow_html=True)

        with col_right:
            st.markdown("### 💬 Data Concierge")
            chat_container = st.container(height=450, border=True)
            
            if "messages" not in st.session_state: st.session_state.messages = []
            
            with chat_container:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]): st.markdown(msg["content"])

            if prompt := st.chat_input("Analyze specific trends..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with chat_container:
                    with st.chat_message("user"): st.markdown(prompt)
                
                context = f"Revenue {m['rev']}, Profit {m['prof']}, Top Item {m['best_seller']}. Question: {prompt}"
                
                with chat_container:
                    with st.chat_message("assistant"):
                        res = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": context}]
                        )
                        answer = res.choices[0].message.content
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        st.error(f"Analysis Interrupted: {e}")
else:
    st.info("⬆️ Upload a file to initialize the Dark Intelligence dashboard.")
