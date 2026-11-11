import json
import logging
import asyncio
from typing import Dict, Any, Optional
import fitz # PyMuPDF
from google import genai
from google.genai import types
from backend.app.config import settings
from backend.app.extraction.base import FactExtractor
from backend.app.resolver.states import PolicyFacts

logger = logging.getLogger(__name__)

GEMINI_SYSTEM_INSTRUCTION = """
You are an expert Indian motor insurance policy schedule analyst.
Extract ground truth policy fields strictly from the provided policy schedule pages.
Do NOT invent or guess values.
If a value is not explicitly stated, return null and note the uncertainty.
For numbers (CC, NCB percent, premiums, age), extract pure numeric values.
Premium fields must be numeric: basicOd, ncbDiscount, netOd, basicTp, netTp, taxes, total.
If registration date is present, extract registrationYear as an integer.
For geography, extract the exact printed RTO code (e.g. 'UP-16', 'DL-9C', 'HR-26') and the exact printed location/address text.
"""

EXTRACTION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "insurer": {
            "type": "OBJECT",
            "properties": {
                "value": {"type": "STRING"},
                "page": {"type": "INTEGER"},
                "confidence": {"type": "NUMBER"}
            },
            "required": ["value", "page", "confidence"]
        },
        "previousInsurer": {
            "type": "OBJECT",
            "properties": {
                "value": {"type": "STRING"},
                "page": {"type": "INTEGER"},
                "confidence": {"type": "NUMBER"},
                "uncertainty": {"type": "STRING"},
                "lowConfidence": {"type": "BOOLEAN"}
            }
        },
        "businessType": {
            "type": "OBJECT",
            "properties": {
                "value": {"type": "STRING"}, # new, renewal, rollover
                "page": {"type": "INTEGER"},
                "confidence": {"type": "NUMBER"},
                "uncertainty": {"type": "STRING"}
            },
            "required": ["value"]
        },
        "policyType": {
            "type": "OBJECT",
            "properties": {
                "value": {"type": "STRING"}, # comprehensive, stand_alone_tp, stand_alone_od
                "page": {"type": "INTEGER"},
                "confidence": {"type": "NUMBER"}
            },
            "required": ["value", "page"]
        },
        "make": {
            "type": "OBJECT",
            "properties": {
                "value": {"type": "STRING"},
                "page": {"type": "INTEGER"}
            },
            "required": ["value"]
        },
        "model": {
            "type": "OBJECT",
            "properties": {
                "value": {"type": "STRING"},
                "page": {"type": "INTEGER"}
            },
            "required": ["value"]
        },
        "fuel": {
            "type": "OBJECT",
            "properties": {
                "value": {"type": "STRING"}, # petrol, diesel, cng, electric
                "page": {"type": "INTEGER"},
                "uncertainty": {"type": "STRING"},
                "lowConfidence": {"type": "BOOLEAN"}
            },
            "required": ["value"]
        },
        "rto": {
            "type": "OBJECT",
            "properties": {
                "value": {"type": "STRING"},
                "page": {"type": "INTEGER"},
                "confidence": {"type": "NUMBER"}
            },
            "required": ["value"]
        },
        "printedLocation": {
            "type": "OBJECT",
            "properties": {
                "value": {"type": "STRING"},
                "page": {"type": "INTEGER"},
                "confidence": {"type": "NUMBER"}
            }
        },
        "engineCc": {
            "type": "OBJECT",
            "properties": {
                "value": {"type": "NUMBER"},
                "page": {"type": "INTEGER"}
            }
        },
        "registrationYear": {
            "type": "OBJECT",
            "properties": {
                "value": {"type": "INTEGER"},
                "page": {"type": "INTEGER"}
            }
        },
        "policyStartDate": {
            "type": "OBJECT",
            "properties": {
                "value": {"type": "STRING"},
                "page": {"type": "INTEGER"}
            }
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
                "page": {"type": "INTEGER"},
                "ncbPercent": {"type": "NUMBER"},
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
        
        # Prepare page images at 100 DPI (crisp, compact payload for fast processing)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_parts = []
        
        # Extract schedule pages (up to first 3 pages and last page)
        pages_to_extract = set()
        for i in range(min(3, len(doc))):
            pages_to_extract.add(i)
        if len(doc) > 3:
            pages_to_extract.add(len(doc) - 1)
            
        for page_idx in sorted(pages_to_extract):
            pix = doc[page_idx].get_pixmap(dpi=100)
            img_bytes = pix.tobytes("jpeg") # JPEG is significantly smaller and faster to send over TLS
            page_parts.append(types.Part.from_bytes(
                data=img_bytes,
                mime_type="image/jpeg"
            ))
            
        prompt = f"Analyze this motor policy document ({file_name}, total {len(doc)} pages). Extract all rating facts following the schema strictly."
        contents = [prompt] + page_parts
        
        # Call API with progressive backoff and fallback model if 503 spike occurs
        max_retries = 3
        candidate_models = [self.model, "gemini-3.5-flash-lite"]
        
        last_error = None
        for current_model in candidate_models:
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=current_model,
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
                        "model_id": current_model,
                        "confidence": 0.92
                    }
                except Exception as e:
                    last_error = e
                    logger.warning(f"Gemini API model {current_model} attempt {attempt+1} failed: {e}")
                    await asyncio.sleep(2 * (attempt + 1))
                    
        raise RuntimeError(f"Gemini extraction failed across models: {last_error}")
