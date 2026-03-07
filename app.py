import streamlit as st
import pandas as pd
import plotly.express as px
import Truemetrics as tm

# --- [ 1. WORLD CLASS UI DESIGN ] ---
st.set_page_config(page_title="TrueMetrics | Pro", page_icon="📈", layout="wide")
BLUE, GOLD, DARK, PANEL = "#3B82F6", "#F59E0B", "#020617", "rgba(255, 255, 255, 0.03)"
# --- [ INITIALIZE SESSION STATE ] ---
if "is_paid" not in st.session_state:
    st.session_state.is_paid = False  # Default to Free tier

if "m" not in st.session_state:
    st.session_state.m = None

if "insight" not in st.session_state:
    st.session_state.insight = None

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Inter:wght@400;500&display=swap');
    .stApp {{ background: {DARK}; color: #f8fafc; font-family: 'Inter', sans-serif; }}
    h1, h2, h3, h4 {{ font-family: 'Outfit', sans-serif !important; margin-bottom: 8px !important; }}
    div[data-testid="stMetric"] {{
        background: {PANEL} !important; border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 16px !important; padding: 20px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}
    .glass-card {{
        background: {PANEL}; border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px; padding: 24px; margin-bottom: 20px;
    }}
    .premium-card {{
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(0,0,0,0));
        border: 1px solid {GOLD}; border-radius: 20px; padding: 25px;
    }}
    .data-warning {{ background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; color: #94a3b8; font-size: 14px; text-align: center; border: 1px dashed rgba(255,255,255,0.1); }}
    </style>
    """, unsafe_allow_html=True)

# --- [ 2. SAFE API INIT ] ---
# --- [ CLIENT INIT ] ---
# Replace the old 'configure_dual_engines' block with this:
MISTRAL_KEY = st.secrets.get("MISTRAL_API_KEY", "")
client = tm.get_mistral_client(MISTRAL_KEY)

# --- [ 3. SIDEBAR / SIMULATION ] ---
with st.sidebar:
    st.markdown("### ⚙️ System Settings")
    user_tier = st.toggle("Simulate Premium Tier", value=st.session_state.is_paid)
    st.session_state.is_paid = user_tier
    st.caption("Toggle to view human-in-the-loop features.")
    st.divider()

# --- [ 4. MAIN DASHBOARD ] ---
st.markdown("<h1 style='font-size:48px; margin-top: -20px;'>TrueMetrics</h1>", unsafe_allow_html=True)
st.caption("Universal POS Intelligence Platform")

if st.session_state.m is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    up = st.file_uploader("Upload any POS Export (CSV/XLSX)", type=["csv", "xlsx"])
    if up:
        try:
            raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
            m_data, _ = tm.process_business_data(raw)
            if m_data.get("error"): st.error(m_data["error"])
            else:
                st.session_state.m = m_data
                st.rerun()
        except Exception as e:
            st.error(f"File readability error: {e}. Please ensure it is a valid table.")
else:
    m = st.session_state.m
    
    if st.sidebar.button("🗑️ Upload New Dataset"):
        st.session_state.m = None
        st.session_state.chat = []
        st.rerun()

    if m.get("warning"):
        st.warning(m["warning"])

    # === NEW KPI STRIP (Including Orders & AOV) ===
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("💰 Revenue", f"{m.get('total_revenue', 0):,.0f}")
    k2.metric("🛍️ Orders", f"{m.get('orders', 0):,}")
    k3.metric("🛒 Avg Order (AOV)", f"{m.get('avg_order_value', 0):,.1f}")
    k4.metric("🎯 Margin", f"{m.get('margin_pct', 0)}%")
    
    fc = m.get('forecast', 0)
    if fc > 0: k5.metric("🔮 30-Day Forecast", f"{fc:,.0f}")
    else: k5.metric("🔮 30-Day Forecast", "N/A")

    st.markdown("<br>", unsafe_allow_html=True)

    # === HUMAN IN THE LOOP (PREMIUM UPSALE) ===
    if st.session_state.is_paid:
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        col_text, col_btn = st.columns([3, 1])
        with col_text:
            st.markdown(f"<h4>🎓 Expert Strategy Call</h4>", unsafe_allow_html=True)
            st.write("Your POS data indicates optimization opportunities. Connect with a human analyst to review these metrics.")
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("📅 Book Session", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='glass-card' style='border: 1px dashed rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
        col_text, col_btn = st.columns([3, 1])
        with col_text:
            st.markdown(f"<h4 style='color:#94a3b8;'>🔒 Unlock Human Advisory</h4>", unsafe_allow_html=True)
            st.write("Upgrade to Premium to have a certified retail analyst review your dashboard weekly.")
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("🚀 Upgrade to Premium", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # === INSIGHTS / INDICATIONS SECTION ===
    c_top, c_risk = st.columns(2)
    loc_title = m.get('loc_header', 'Segment')
    
    with c_top:
        st.markdown("<div class='glass-card' style='height: 280px;'>", unsafe_allow_html=True)
        st.markdown(f"<h4>⭐ Top Performers ({loc_title})</h4>", unsafe_allow_html=True)
        top_list = m.get('top_margins', [])
        if top_list:
            for i in top_list: st.success(f"▲ {i}")
        else:
            st.markdown("<div class='data-warning'>Not sufficient category/location data to calculate top performers.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with c_risk:
        st.markdown("<div class='glass-card' style='height: 280px;'>", unsafe_allow_html=True)
        st.markdown(f"<h4>⚠️ Margin Risks ({loc_title})</h4>", unsafe_allow_html=True)
        bot_list = m.get('bot_margins', [])
        if bot_list:
            for i in bot_list: st.error(f"▼ {i}")
        else:
            st.markdown("<div class='data-warning'>Not sufficient category/location data to identify risks.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # === TREND PREDICTION CHART ===
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h4>📊 Revenue Timeline & Trajectory</h4>", unsafe_allow_html=True)
    if m.get('trend_data'):
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
        fig = px.area(tdf, x='Date', y='Sales')
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=300, margin=dict(l=0, r=0, t=10, b=0))
        fig.update_traces(line_color=BLUE, fillcolor='rgba(59, 130, 246, 0.1)', line_width=3)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("<br><div class='data-warning'>Not sufficient date/time data found in the file to plot historical trends.</div><br>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # === DATA MAPPING META ===
    with st.expander(f"🧬 Engine Mapping Confidence: {m.get('confidence', 0)}%", expanded=False):
        st.write("How the AI interpreted your raw file:")
        if m.get('mapping_preview'):
            st.table(pd.DataFrame(m['mapping_preview']))
        else:
            st.write("No column mapping was successful.")

    # === AI CHAT POPOVER ===
    with st.popover("💬 Ask AI Analyst"):
        if not m_client: 
            st.error("Mistral API Key missing in secrets.toml")
        else:
            chat_box = st.container(height=300)
            for msg in st.session_state.chat:
                with chat_box.chat_message(msg["role"]): st.write(msg["content"])
            
            if p := st.chat_input("Ask: 'Why did my AOV drop?'"):
                st.session_state.chat.append({"role": "user", "content": p})
                st.session_state.chat.append({"role": "assistant", "content": tm.get_ai_response(m_client, m, p, st.session_state.is_paid)})
                st.rerun()



