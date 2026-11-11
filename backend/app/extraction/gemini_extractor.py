import json
import logging
import asyncio
from typing import Dict, Any, List
import fitz # PyMuPDF
from google import genai
from google.genai import types
from backend.app.config import settings
from backend.app.extraction.base import FactExtractor
from backend.app.resolver.states import PolicyFacts, FactField, PremiumBreakup

logger = logging.getLogger(__name__)

GEMINI_SYSTEM_INSTRUCTION = """You are an expert insurance policy document reader. 
Extract policy facts accurately into the required JSON schema. 
Rules:
1. Every extracted field MUST specify its physical PDF page number (1-based), confidence (0.0 to 1.0), and uncertainty notes if any.
2. Never invent values. If a field is not printed or unpopulated (e.g. 0001-01-01), set value to null and document uncertainty.
3. Extract registrationYear from registration date or year field. Do NOT invent fake days/months (like 2019-01-01) if only a year is given.
4. Extract all premium items: basic OD, NCB discount amount and percentage, net OD, basic TP, net TP, taxes, and total payable premium.
5. Extract exact printed location text (city, state, PIN code) from schedule.
"""

EXTRACTION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "insurer": {
            "type": "OBJECT",
            "properties": {"value": {"type": "STRING"}, "page": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}, "uncertainty": {"type": "STRING"}},
            "required": ["value", "page", "confidence"]
        },
        "previousInsurer": {
            "type": "OBJECT",
            "properties": {"value": {"type": "STRING"}, "page": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}, "uncertainty": {"type": "STRING"}}
        },
        "businessType": {
            "type": "OBJECT",
            "properties": {"value": {"type": "STRING", "enum": ["new", "renewal", "rollover", "unknown"]}, "page": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}, "uncertainty": {"type": "STRING"}},
            "required": ["value", "page", "confidence"]
        },
        "policyType": {
            "type": "OBJECT",
            "properties": {"value": {"type": "STRING", "enum": ["comprehensive", "stand_alone_tp", "stand_alone_od"]}, "page": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}},
            "required": ["value", "page", "confidence"]
        },
        "make": {
            "type": "OBJECT",
            "properties": {"value": {"type": "STRING"}, "page": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}},
            "required": ["value", "page"]
        },
        "model": {
            "type": "OBJECT",
            "properties": {"value": {"type": "STRING"}, "page": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}},
            "required": ["value", "page"]
        },
        "fuel": {
            "type": "OBJECT",
            "properties": {"value": {"type": "STRING"}, "page": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}, "uncertainty": {"type": "STRING"}},
            "required": ["value", "page"]
        },
        "rto": {
            "type": "OBJECT",
            "properties": {"value": {"type": "STRING"}, "page": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}},
            "required": ["value", "page"]
        },
        "printedLocation": {
            "type": "OBJECT",
            "properties": {"value": {"type": "STRING"}, "page": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}},
            "required": ["value", "page"]
        },
        "engineCc": {
            "type": "OBJECT",
            "properties": {"value": {"type": "NUMBER"}, "page": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}}
        },
        "registrationYear": {
            "type": "OBJECT",
            "properties": {"value": {"type": "INTEGER"}, "page": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}}
        },
        "manufactureYear": {
            "type": "OBJECT",
            "properties": {"value": {"type": "INTEGER"}, "page": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}, "uncertainty": {"type": "STRING"}}
        },
        "policyStartDate": {
            "type": "OBJECT",
            "properties": {"value": {"type": "STRING"}, "page": {"type": "INTEGER"}, "confidence": {"type": "NUMBER"}}
        },
        "premiums": {
            "type": "OBJECT",
            "properties": {
                "basicOd": {"type": "NUMBER"},
                "ncbDiscount": {"type": "NUMBER"},
                "netOd": {"type": "NUMBER"},
                "basicTp": {"type": "NUMBER"},
                "netTp": {"type": "NUMBER"},
                "taxes": {"type": "NUMBER"},
                "total": {"type": "NUMBER"},
                "ncbPercent": {"type": "NUMBER"},
                "ncbUnclearNote": {"type": "STRING"},
                "page": {"type": "INTEGER"},
                "confidence": {"type": "NUMBER"}
            },
            "required": ["total", "page"]
        }
    },
    "required": ["insurer", "policyType", "make", "model", "rto", "premiums"]
}

class GeminiFactExtractor(FactExtractor):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not configured in settings.")
            
    async def extract_facts(self, pdf_bytes: bytes, file_name: str) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing. Please set GEMINI_API_KEY in rater/.env.")
            
        client = genai.Client(api_key=self.api_key)
        
        # Prepare page images
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_parts = []
        
        # Extract up to first 5 pages and last 2 pages (to capture proposal transcripts)
        pages_to_extract = set()
        for i in range(min(5, len(doc))):
            pages_to_extract.add(i)
        for i in range(max(0, len(doc) - 2), len(doc)):
            pages_to_extract.add(i)
            
        for page_idx in sorted(pages_to_extract):
            pix = doc[page_idx].get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            page_parts.append(types.Part.from_bytes(
                data=img_bytes,
                mime_type="image/png"
            ))
            
        prompt = f"Analyze this motor policy document ({file_name}, total {len(doc)} pages). Extract all rating facts following the schema strictly."
        contents = [prompt] + page_parts
        
        # Call API with retry and backoff
        max_retries = 3
        raw_response_text = ""
        
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=GEMINI_SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        response_schema=EXTRACTION_SCHEMA,
                        temperature=0.0
                    )
                )
                raw_response_text = response.text
                data = json.loads(raw_response_text)
                
                # Derive vehicleAgeYears
                reg_year = data.get("registrationYear", {}).get("value")
                start_date = data.get("policyStartDate", {}).get("value", "")
                age_val = None
                if reg_year and start_date and len(start_date) >= 4:
                    try:
                        pol_yr = int(start_date[:4])
                        age_val = max(0, pol_yr - int(reg_year))
                    except Exception:
                        pass
                elif reg_year:
                    age_val = max(0, 2026 - int(reg_year))
                    
                data["vehicleAgeYears"] = {
                    "value": age_val,
                    "page": data.get("registrationYear", {}).get("page"),
                    "confidence": 0.95
                }
                
                # Cross-check business type: insurer vs previous insurer
                curr_ins = (data.get("insurer", {}).get("value") or "").upper()
                prev_ins = (data.get("previousInsurer", {}).get("value") or "").upper()
                if curr_ins and prev_ins and any(w in curr_ins for w in prev_ins.split() if len(w) > 3):
                    data["businessType"]["value"] = "renewal"
                elif prev_ins and not any(w in curr_ins for w in prev_ins.split() if len(w) > 3):
                    data["businessType"]["value"] = "rollover"
                    
                facts_obj = PolicyFacts(**data)
                
                return {
                    "facts": facts_obj,
                    "raw_json": raw_response_text,
                    "model_id": self.model,
                    "confidence": 0.92
                }
            except Exception as e:
                logger.warning(f"Gemini API attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Gemini extraction failed after {max_retries} attempts: {e}")
                await asyncio.sleep(2 ** attempt)
