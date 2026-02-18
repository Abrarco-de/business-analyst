# --- CHATBOT SECTION ---
st.divider()
st.subheader("💬 Chat with your Business Data")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about your sales, trends, or VAT..."):
    # 1. Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Prepare Context for the AI
    # We feed the AI the metrics we already calculated earlier (m)
    context = f"""
    Context: You are analyzing a business dataset.
    - Columns: {list(df_final.columns)}
    - Summary Metrics: Revenue={m['rev']}, Profit={m['prof']}, Best Seller={m['best_seller']}
    - User Query: {prompt}
    Based on these numbers, give a specific answer. If you need to suggest a calculation, explain how to do it.
    """

    # 3. Get AI Response from Groq
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # We reuse your existing groq_client
            try:
                chat_completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a data analyst. Use the provided metrics to answer questions accurately."},
                        {"role": "user", "content": context}
                    ],
                    temperature=0.2 # Keep it focused on facts
                )
                response = chat_completion.choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error("Chat Error: Ensure Groq API Key is valid.")
