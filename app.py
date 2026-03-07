import streamlit as st
import pandas as pd
import Truemetrics as tm

# 1. PAGE CONFIG
st.set_page_config(page_title="TrueMetrics | Advisor", page_icon="🤝", layout="centered")

# 2. INITIALIZE SESSION STATE (Prevents AttributeError)
if "m" not in st.session_state:
    st.session_state.m = None
if "insight" not in st.session_state:
    st.session_state.insight = None
if "is_paid" not in st.session_state:
    st.session_state.is_paid = False

# 3. UI STYLING (Consultant Vibe)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;600&display=swap');
    .stApp { background-color: #020617; color: #f8fafc; }
    .briefing-card {
        background: #0f172a; border: 1px solid #1e293b;
        border-radius: 28px; padding: 40px; margin-bottom: 30px;
        line-height: 1.8; font-size: 18px; font-weight: 300;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .kpi-container { display: flex; justify-content: space-between; margin-top: 20px; }
    .kpi-box { text-align: center; flex: 1; }
    .kpi-label { color: #64748b; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value { font-family: 'Outfit'; font-size: 24px; font-weight: 600; color: #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

# 4. INITIALIZE CLIENT (Matches variable names to prevent NameError)
MISTRAL_KEY = st.secrets.get("MISTRAL_API_KEY", "")
m_client = tm.get_mistral_client(MISTRAL_KEY)

# 5. HEADER
st.markdown("<h2 style='text-align:center; font-family:Outfit;'>TrueMetrics</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#64748b;'>Your Digital Business Advisor</p>", unsafe_allow_html=True)

# 6. APP LOGIC
if st.session_state.m is None:
    st.markdown("<br>", unsafe_allow_html=True)
    up = st.file_uploader("Upload your sales report to begin the briefing...", type=["csv", "xlsx"])
    
    if up:
        # Load data
        try:
            raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
            m_data, _ = tm.process_business_data(raw)
            
            if m_data.get("error"):
                st.error(m_data["error"])
            else:
                st.session_state.m = m_data
                # Generate human insight
                if not m_client:
                    st.error("Missing Mistral API Key. Check your secrets.toml.")
                else:
                    with st.spinner("Your advisor is interpreting the data..."):
                        st.session_state.insight = tm.get_consultant_insight(m_client, m_data["raw_metrics"])
                    st.rerun()
        except Exception as e:
            st.error(f"The file could not be read: {e}")

else:
    # THE BRIEFING (The "Hero" of the USP)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<div class='briefing-card'>{st.session_state.insight}</div>", unsafe_allow_html=True)

    # THE SUBTLE METRICS (Supporting the story)
    m = st.session_state.m
    st.markdown("<div class='kpi-container'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='kpi-box'><p class='kpi-label'>Total Revenue</p><p class='kpi-value'>{m['raw_metrics']['total_revenue']:,.0f}</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='kpi-box'><p class='kpi-label'>Avg Order Value</p><p class='kpi-value'>{m['raw_metrics']['aov']:.1f}</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='kpi-box'><p class='kpi-label'>Profit Margin</p><p class='kpi-value'>{m['raw_metrics']['margin']:.1f}%</p></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 7. PREMIUM UPSALE
    st.markdown("<div style='background:#0f172a; padding:25px; border-radius:20px; border: 1px dashed #334155;'>", unsafe_allow_html=True)
    st.markdown("**Unlock Deep Insights**")
    st.write("This AI briefing covers the basics. For a full audit including waste detection and staff performance, connect with a human analyst.")
    if st.button("Request Human Audit", use_container_width=True):
        st.success("Request sent! A retail analyst will review your data within 24 hours.")
    st.markdown("</div>", unsafe_allow_html=True)

    # 8. RESET SIDEBAR
    if st.sidebar.button("🗑️ Analyze New Report"):
        st.session_state.m = None
        st.session_state.insight = None
        st.rerun()
