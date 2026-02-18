def get_intelligent_answer(groq_client, df, user_query, m):
    try:
        # ROLE 1: Groq (Data Researcher)
        # Groq doesn't have 404 naming issues, so we use it for the heavy lifting
        data_summary = df.head(100).to_string()
        research_prompt = f"Analyze for query: {user_query}. Data: {data_summary}"
        
        research = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": research_prompt}]
        )
        fact_sheet = research.choices[0].message.content

        # ROLE 2: Gemini (Consultant) - Updated for 2026
        # We try the most stable 2026 IDs in order
        target_models = ['gemini-2.5-flash', 'gemini-3-flash-preview', 'gemini-2.0-flash']
        
        model = None
        for model_id in target_models:
            try:
                model = genai.GenerativeModel(model_id)
                # Test call to verify if model exists
                model.generate_content("test", generation_config={"max_output_tokens": 1})
                break 
            except:
                continue
        
        if not model:
            return "AI Bridge Error: No compatible Gemini models found for your API key."

        consultant_prompt = f"""
        Fact Sheet: {fact_sheet}
        Stats: Revenue {m['rev']} SAR, Profit {m['prof']} SAR.
        User: {user_query}
        Provide a strategic Saudi business answer.
        """
        response = model.generate_content(consultant_prompt)
        return response.text

    except Exception as e:
        return f"System Error: {str(e)}"
