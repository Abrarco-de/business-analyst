import pandas as pd
import numpy as np
import google.generativeai as genai
from groq import Groq
import json, re, difflib

# --- 1. CONFIGURATION ---
def configure_engines(gemini_key, groq_key):
    try:
        genai.configure(api_key=gemini_key)
        return Groq(api_key=groq_key)
    except: return None

# --- 2. DATA CLEANING & MAPPING (Keep existing robust logic) ---
def calculate_precise_metrics(df):
    # (Keeping the same metric calculation logic we built before)
    df.columns = [str(c).strip() for c in df.columns]
    # ... [Rest of your calculation logic here] ...
    # Let's assume 'm' is your metrics dict and 'df' is cleaned
    return m, df 

# --- 3. THE SWAPPED INTELLIGENCE BRIDGE ---
def get_intelligent_answer(groq_client, df, user_query, metrics):
    try:
        # ROLE 1: Groq (The Data Researcher) - Scans rows because it's fast & reliable
        data_snapshot = df.head(100).to_string() # Groq handles large text well
        
        research_prompt = f"""
        You are a Data Scraper. Look at this user query: "{user_query}"
        Dataset Snapshot:
        {data_snapshot}
        
        Task: Extract specific numbers, product names, and dates related to the query. 
        Provide a raw 'Fact Sheet'.
        """
        
        # Calling Groq first for research
        groq_research = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": research_prompt}],
            temperature=0.1
        )
        fact_sheet = groq_research.choices[0].message.content

        # ROLE 2: Gemini (The Executive Analyst) - Provides the final business advice
        # We use a very simple model call here to avoid the 404 versioning issue
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        analysis_prompt = f"""
        Fact Sheet from Research: {fact_sheet}
        High-Level Metrics: Revenue {metrics['rev']}, Profit {metrics['prof']}
        
        Question: {user_query}
        
        Task: Based on the facts, give a professional business answer. 
        Focus on 'Why' this is happening and give 1 Saudi-market strategy tip.
        """
        
        # Gemini provides the final "Brain" output
        gemini_response = model.generate_content(analysis_prompt)
        return gemini_response.text

    except Exception as e:
        return f"Role-Swap Error: {str(e)}"

