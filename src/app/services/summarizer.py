from abc import ABC, abstractmethod
import requests
from app.config import settings
import json


class BaseSummarizer(ABC):    
    @abstractmethod
    def generate(self,text:str)->dict:
        pass

class MockSummarizer(BaseSummarizer):
    def generate(self, text: str) -> dict:
        lines = text.split(".")
        summary = " ".join(lines[:3]).strip()
        action_items= []
        decisions = []
        for line in lines:
            if any(word in line.lower() for word in ["action", "will", "should", "must"]):
                action_items.append(line.strip())
            if any(word in line.lower() for word in ["decided", "agreed", "approved"]):
                decisions.append(line.strip())
        return {
            "summary"  : summary,
            "action_items" : action_items , 
            "decisions" : decisions
        }
    

class GroqSummarizer(BaseSummarizer):
    def generate(self, text: str) -> dict:
        prompt = f"""You are analyzing a meeting transcript. Return ONLY a valid JSON object (no markdown, no explanation) with exactly these three keys:

        - "summary": a concise 3-5 sentence summary of what was discussed
        - "action_items": a JSON array of strings, each a specific task someone committed to doing (empty array if none)
        - "decisions": a JSON array of strings, each a concrete decision the group agreed on (empty array if none)
        
        Transcript:
        {text[:8000]}
        """
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"},
                },
                timeout=30,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            return {
                "summary": parsed.get("summary", ""),
                "action_items": parsed.get("action_items", []),
                "decisions": parsed.get("decisions", []),
            }
        except Exception as e:
            raise RuntimeError(f"Groq API error: {str(e)}")
class HuggingFaceSummarizer(BaseSummarizer):
    def generate(self, text: str) -> dict:
        try:
            response = requests.post(
                "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
                headers= {"Authorization": f"Bearer {settings.HF_API_TOKEN}"},
                json = {"inputs": text[:1024]},
                timeout=30,
            )
            response.raise_for_status()
            summary = response.json()[0]["summary_text"]
            return {"summary": summary, "action_items": [], "decisions": []}
        
        except Exception as e:
            raise RuntimeError(f"HuggingFace API error {str(e)}")

def get_summarizer() -> BaseSummarizer:
    if settings.SUMMARIZER_TYPE == "mock":
        return MockSummarizer()
    elif settings.SUMMARIZER_TYPE == "huggingface":
        return HuggingFaceSummarizer()
    elif settings.SUMMARIZER_TYPE == "groq":
        return GroqSummarizer()
    raise ValueError(f"Unknown summarizer type: {settings.SUMMARIZER_TYPE}")