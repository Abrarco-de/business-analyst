import streamlit as st
import google.generativeai as genai
import time
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="SME Analyst Pro", layout="wide")

# 1. API Initialization
if "GEMINI_API_KEY" in st.secrets:
    ai_status = configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    st.sidebar.error("Key missing in Secrets!")
    ai_status = False

st.title("📈 Visionary SME Analyst")

# 2. File Upload
file = st.file_uploader("Upload Sales Data", type=["csv", "xlsx"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None:
        # --- SIDEBAR OVERRIDE ---
        st.sidebar.header("🛠️ Column Settings")
        st.sidebar.write("If numbers look wrong, adjust these:")
        
        all_cols = list(df_raw.columns)
        auto_map = get_header_mapping(all_cols)
        
        # Helper to find default index
        def get_idx(key, default_val):
            found = [k for k, v in auto_map.items() if v == key]
            return all_cols.index(found[0]) if found and found[0] in all_cols else all_cols.index(default_val)

        selected_prod = st.sidebar.selectbox("Product/Category Column", all_cols, index=0)
        selected_rev = st.sidebar.selectbox("Revenue/Total Sales Column", all_cols, index=min(1, len(all_cols)-1))
        selected_qty = st.sidebar.selectbox("Quantity Column", all_cols, index=min(2, len(all_cols)-1))
        selected_prof = st.sidebar.selectbox("Profit Column (Optional)", ["None"] + all_cols)

        # Apply Overrides
        overrides = {
            "product_name": selected_prod,
            "total_amount": selected_rev,
            "quantity": selected_qty,
            "cost_price": selected_prof if selected_prof != "None" else "cost_price"
        }

        # 3. Calculate Results
        res = generate_insights(df_raw, mapping_overrides=overrides)

        # 4. Display Dashboard
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Revenue", f"{res['revenue']:,} SAR")
        col2.metric("Total Profit", f"{res['profit']:,} SAR")
        col3.metric("Profit Margin", f"{res['margin']}%")
        col4.metric("Best Seller", res['best_seller'])

        st.divider()

        # 5. Visuals & AI Insight
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Sales Distribution")
            if res['revenue'] > 0:
                chart_data = res['df'].groupby(res['name_col'])['temp_rev'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(chart_data)

        with c2:
            st.subheader("AI Strategic Consultant")
            if st.button("✨ Generate AI Insights"):
                if ai_status and res['revenue'] > 0:
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = f"Business context: Revenue {res['revenue']} SAR, Profit {res['profit']} SAR, Top Item {res['best_seller']}. Provide 3 short growth strategies."
                        response = model.generate_content(prompt)
                        st.info(response.text)
                    except Exception as e:
                        if "429" in str(e) or "overloaded" in str(e).lower():
                            st.error("🚨 AI is overloaded. Please wait 30 seconds (Google's free tier limit) and click again.")
                        else:
                            st.error("AI connection error. Try again shortly.")
                else:
                    st.warning("Ensure data is correct and API key is set.")




