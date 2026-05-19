import os
import google.generativeai as genai

class GeminiClient:
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        prompt = f"{system_prompt}\n\nUser:\n{user_prompt}"
        resp = self.model.generate_content(prompt)
        return resp.text.strip()
