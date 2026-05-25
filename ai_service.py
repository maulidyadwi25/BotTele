import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
load_dotenv()  # Load .env

class AIProvider:
    """Base class untuk semua provider AI"""
    def generate_response(self, system_prompt: str, user_message: str) -> str:
        raise NotImplementedError

class GoogleAIProvider(AIProvider):
    def __init__(self):
        # Cara baru menginisialisasi client
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
    
    def generate_response(self, system_prompt: str, user_message: str) -> str:
        # Gunakan API terbaru
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"{system_prompt}\n\nPertanyaan pengguna: {user_message}",
        )
        return response.text

class OpenRouterProvider(AIProvider):
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    
    def generate_response(self, system_prompt: str, user_message: str) -> str:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
        )
        return completion.choices[0].message.content

class OpenAICompatibleProvider(AIProvider):
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_COMPATIBLE_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY"),
        )
        self.model = os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-4o-mini")
    
    def generate_response(self, system_prompt: str, user_message: str) -> str:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
        )
        return completion.choices[0].message.content

def get_ai_provider() -> AIProvider:
    """Factory function untuk mendapatkan provider berdasarkan konfigurasi"""
    provider_name = os.getenv("AI_PROVIDER", "openrouter").lower()
    
    if provider_name == "google":
        return GoogleAIProvider()
    elif provider_name == "openrouter":
        return OpenRouterProvider()
    elif provider_name == "openai_compatible":
        return OpenAICompatibleProvider()
    else:
        raise ValueError(f"Provider tidak dikenal: {provider_name}. Pilih: google, openrouter, openai_compatible")