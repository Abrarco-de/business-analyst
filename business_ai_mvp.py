import os
import google.generativeai as genai

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not set")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")


