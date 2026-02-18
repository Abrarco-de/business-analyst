def get_intelligent_answer(groq_client, df, user_query, m):
    try:
        import google.generativeai as genai
        
        # --- 1. RESEARCH (Groq) ---
        # We use Groq for the research because it's reliable and fast.
        data_sample = df.head(100).to_string()
        research_prompt = f"Analyze for query: {user_query}. Data: {data_sample}"
        
        research = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": research_prompt}]
        )
        fact_sheet = research.choices[0].message.content

        # --- 2. DYNAMIC MODEL DISCOVERY (Gemini) ---
        # Instead of guessing the name, we find what's available
        available_models = [m.name for m in genai.list_models() 
                           if 'generateContent' in m.supported_generation_methods]
        
        # Pick the best one available (prioritizing Gemini 3 or 2.5)
        selected_model = "gemini-1.5-flash" # Fallback default
        for model_name in ["models/gemini-3-flash", "models/gemini-2.5-flash", "models/gemini-1.5-flash-latest"]:
            if model_name in available_models:
                selected_model = model_name
                break
        
        model = genai.GenerativeModel(selected_model)
        
        # --- 3. FINAL CONSULTATION ---
        consultant_prompt = f"""
        Fact Sheet: {fact_sheet}
        SME Stats: Revenue {m['rev']} SAR, Profit {m['prof']} SAR.
        User: {user_query}
        Provide a professional business answer for a Saudi SME.
        """
        response = model.generate_content(consultant_prompt)
        return response.text

    except Exception as e:
        return f"System Error: {str(e)}"
