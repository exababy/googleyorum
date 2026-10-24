"""Gemini ile yorum cevabı üretir."""
from google import genai
from google.genai import types


class ReplyGenerator:
    def __init__(self, api_key: str, model: str, system_prompt: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.system_prompt = system_prompt

    def generate(self, reviewer: str, stars: int, comment: str) -> str:
        user_msg = (
            f"Müşteri adı: {reviewer or 'Bilinmiyor'}\n"
            f"Puan: {stars}/5\n"
            f"Yorum: {comment or '(Müşteri yorum yazmadan sadece puan verdi)'}\n\n"
            "Bu yoruma işletme adına yazılacak cevabı yaz. "
            "Sadece cevap metnini döndür, başka açıklama ekleme."
        )
        resp = self.client.models.generate_content(
            model=self.model,
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                temperature=0.7,
            ),
        )
        text = (resp.text or "").strip()
        if not text:
            raise RuntimeError("Gemini boş cevap döndürdü")
        # Google cevap limiti 4096 karakter
        return text[:4000]

    def list_models(self) -> list[str]:
        return [
            m.name for m in self.client.models.list()
            if "generateContent" in (m.supported_actions or [])
        ]
