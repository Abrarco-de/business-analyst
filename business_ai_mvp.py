import os
import pandas as pd
import google.generativeai as genai


# ---------- INTERNAL: Lazy Gemini Setup ----------
def _get_model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in Streamlit Secrets")

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


# ---------- FILE PROCESSING ----------
def process_business_file(uploaded_file):
    """
    Accepts CSV / Excel file from Streamlit uploader
    Returns pandas DataFrame
    """
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file type")

    return df


# ---------- AI INSIGHTS ----------
def generate_insights(df: pd.DataFrame):
    """
    Sends summarized data to Gemini and returns insights text
    """
    model = _get_model()

    summary = df.describe(include="all").fillna("").to_string()

    prompt = f"""
You are an expert business analyst.
Analyze the following business data summary and give:
1. Key observations
2. Possible errors or anomalies
3. Actionable insights

DATA SUMMARY:
{summary}
"""

    response = model.generate_content(prompt)
    return response.text

