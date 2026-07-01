from abc import ABC, abstractmethod
import requests
from app.config import settings

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
    

class HuggingFaceSummarizer(BaseSummarizer):
    def generate(self, text: str) -> dict:
        try:
            response = requests.post(
                "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
                headers= {"Authorization": f"Bearer {settings.HF_API_TOKEN}"},
                json = {"inputs": text[:1024]}
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
    raise ValueError(f"Unknown summarizer type: {settings.SUMMARIZER_TYPE}")