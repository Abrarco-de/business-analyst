import streamlit as st
import business_ai_mvp as ai


st.set_page_config(
    page_title="AI Business Analyst",
    layout="wide"
)

st.title("📊 AI Business Analyst (MVP)")

st.markdown(
    "Upload your business report (CSV / Excel) and get AI-driven insights."
)

uploaded_file = st.file_uploader(
    "Upload business file",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file:
    try:
        df = ai.process_business_file(uploaded_file)

        st.subheader("Preview Data")
        st.dataframe(df.head())

        if st.button("Generate AI Insights"):
            with st.spinner("Analyzing with AI..."):
                insights = ai.generate_insights(df)

            st.subheader("AI Insights")
            st.write(insights)

    except Exception as e:
        st.error(str(e))






