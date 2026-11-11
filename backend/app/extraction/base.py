from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from backend.app.resolver.states import PolicyFacts

class FactExtractor(ABC):
    @abstractmethod
    async def extract_facts(self, pdf_bytes: bytes, file_name: str) -> Dict[str, Any]:
        """
        Extracts policy facts from PDF bytes.
        Returns a dict containing 'facts' (PolicyFacts), 'raw_json', 'model_id', and 'confidence'.
        """
        pass
