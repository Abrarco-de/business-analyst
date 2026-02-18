import streamlit as st
import pandas as pd
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

st.set_page_config(page_title="AI Business Strategist", layout="wide")

# --- 1. SESSION STATE INITIALIZATION (Prevents KeyErrors) ---
if "messages" not in st.session_state: st.session_state.messages = []
if "m" not in st.session_state: 
    st.session_state.m = {
        "rev": 0, "prof": 0, "margin": 0, "vat": 0, 
        "best_product": "Upload a file to see insights"
    }
if "df_final" not in st.session_state: st.session_state.df_final = None

# --- 2. SIDEBAR CONFIG ---
with st.sidebar:
    st.title("Settings")
    g_key = st.secrets.get("GROQ_API_KEY")
    m_key = st.secrets.get("MISTRAL_API_KEY")
    g_client, m_client = configure_dual_engines(g_key, m_key)
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 3. DATA UPLOAD ---
st.title("💎 Visionary SME AI Dashboard")
uploaded_file = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx"])

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
    with st.spinner("Analyzing your data..."):
        m, df_cleaned = process_business_data(g_client, df_raw)
        st.session_state.m = m
        st.session_state.df_final = df_cleaned

# --- 4. ADVANCED METRIC CARDS ---
m = st.session_state.m
c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue (SAR)", f"{m.get('rev', 0):,}")
c2.metric("Net Profit", f"{m.get('prof', 0):,}")
c3.metric("Profit Margin", f"{m.get('margin', 0)}%")
c4.metric("Top Item", m.get('best_product', 'N/A').split('(')[0])

# --- 5. CHATBOT WITH DATA EXCHANGE ---
st.subheader("💬 AI Strategy Chat")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.write(msg["content"])

if prompt := st.chat_input("Ex: Which product is most profitable?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)
    
    # Fast response for simple thanks
    if any(word in prompt.lower() for word in ["thanks", "shukran", "bye"]):
        response = "Happy to help! Let me know if you need anything else."
    else:
        with st.chat_message("assistant"):
            # CORRECTED: Passing 4 arguments (client, metrics, df, prompt)
            response = get_ai_response(m_client, st.session_state.m, st.session_state.df_final, prompt)
            st.write(response)
            
    st.session_state.messages.append({"role": "assistant", "content": response})
    
