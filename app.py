import streamlit as st
import pandas as pd
from business_ai_mvp import configure_engines, calculate_precise_metrics, groq_get_insights

# 1. Page Configuration
st.set_page_config(
    page_title="Visionary Analyst", 
    page_icon="💎", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS for Professional Styling
st.markdown("""
    <style>
    /* Main background */
    .stApp { background-color: #f8f9fa; }
    
    /* Card styling */
    div[data-testid="stMetricValue"] { font-size: 28px; color: #1E3A8A; font-weight: 700; }
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
    }
    
    /* Title styling */
    .main-title { color: #1E3A8A; font-size: 3rem; font-weight: 800; margin-bottom: 0.5rem; }
    .sub-text { color: #6B7280; font-size: 1.1rem; margin-bottom: 2rem; }
    
    /* Chat styling */
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar for Setup
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1541/1541415.png", width=80)
    st.title("Settings")
    st.info("System: Gemini 1.5 + Llama 3.3")
    
    # Secrets Check
    GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
    GROQ_KEY = st.secrets.get("GROQ_API_KEY")
    
    if not GEMINI_KEY or not GROQ_KEY:
        st.error("⚠️ Missing API Keys in Secrets!")
    
    groq_client = configure_engines(GEMINI_KEY, GROQ_KEY)
    
    st.divider()
    st.write("### Data Controls")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# 4. Main Header
st.markdown('<h1 class="main-title">💎 Visionary SME Analyst</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Intelligent Data Mapping • Precise Math • Strategic Insights</p>', unsafe_allow_html=True)

# 5. File Upload Section
upload_card = st.container()
with upload_card:
    uploaded_file = st.file_uploader("📂 Drop your business records here", type=["csv", "xlsx"])

if uploaded_file:
    try:
        # Load Data
        df_input = pd.read_csv(uploaded_file, encoding='latin1') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        # Logic Processing with Progress status
        with st.status("🚀 Processing Enterprise Intelligence...", expanded=True) as status:
            st.write("🧠 Mapping schema using Gemini...")
            m, df_final = calculate_precise_metrics(df_input)
            
            # Save to session state
            st.session_state['m'] = m
            st.session_state['df_final'] = df_final
            st.session_state['data_loaded'] = True
            status.update(label="✅ Analysis Complete", state="complete")

        # --- Dashboard UI ---
        st.markdown("### 📊 Business Performance Overview")
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            st.metric("Total Revenue", f"{m['rev']:,.0f} SAR", help="Sum of all sales records")
        with m2:
            st.metric("Total Profit", f"{m['prof']:,.0f} SAR", delta=f"{round((m['prof']/m['rev'])*100, 1)}% Margin")
        with m3:
            st.metric("ZATCA VAT", f"{m['vat']:,.0f} SAR", help="15% VAT Liability")
        with m4:
            st.metric("Top Category", m['best_seller'][:15], help="Highest revenue generator")

        st.divider()

        # --- Interactive Insights Section ---
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("💡 Strategic Narrative")
            if st.button("✨ Generate Executive Insights", use_container_width=True):
                with st.spinner("Llama 3 is analyzing trends..."):
                    advice = groq_get_insights(groq_client, m)
                    st.info(advice)
            
            st.subheader("📈 Revenue Concentration")
            chart_data = df_final.groupby(m['p_col'])['_rev'].sum().sort_values(ascending=False).head(10)
            st.bar_chart(chart_data, color="#1E3A8A")

        with col_right:
            # --- CHATBOT UI ---
            st.subheader("💬 Data Concierge")
            chat_container = st.container(height=450, border=True)
            
            if "messages" not in st.session_state:
                st.session_state.messages = []

            with chat_container:
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

            if prompt := st.chat_input("Ask a question about your data..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with chat_container:
                    with st.chat_message("user"):
                        st.markdown(prompt)

                # Contextual prompt for Groq
                context = f"Revenue: {m['rev']}, Profit: {m['prof']}, Top Item: {m['best_seller']}. Question: {prompt}"

                with chat_container:
                    with st.chat_message("assistant"):
                        try:
                            res = groq_client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[{"role": "system", "content": "You are a concise business analyst."},
                                          {"role": "user", "content": context}]
                            )
                            response = res.choices[0].message.content
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        except:
                            st.error("Service error.")

    except Exception as e:
        st.error(f"System Error: {e}")
else:
    # Landing Page Visual if no file is uploaded
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.markdown("### 🔍\n**Smart Mapping**\nGemini identifies your columns automatically.")
    c2.markdown("### 🧮\n**Precise Logic**\nPython ensures 100% accurate financial math.")
    c3.markdown("### 🤖\n**AI Chat**\nLlama 3 answers business queries in real-time.")
