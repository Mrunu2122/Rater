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
CRITICAL NULL POLICY:
- If a value is not explicitly stated on the page, the "value" field MUST be JSON null (or omitted).
- NEVER put sentences like "not printed on policy", "unknown", "null", or explanations inside any "value" field!
- Put explanations, quotes, and reasoning exclusively inside the "uncertainty" field.

For fuel type:
- If the fuel type (e.g. 'Petrol', 'Diesel', 'CNG', 'Electric') is explicitly printed anywhere on the pages, extract that word (e.g. 'CNG' or 'Petrol').
- If no fuel type word is printed anywhere on the document, set value to null and uncertainty to "Fuel type not printed on policy".

For previousInsurer:
- Search all proposal and schedule pages (look for "Previous Insurer", "Full Name of previous insurer", "Previous Policy Details", "Transcript of Proposal").
- Extract the exact insurer name if found, with its page number.
- If not stated anywhere, set value to null.

For businessType:
- If previousInsurer is null, set value to "unknown".
- If previousInsurer is the same insurer as the current policy, set value to "renewal".
- If previousInsurer is a different insurer, set value to "rollover".

For numbers (CC, NCB percent, premiums, age), extract pure numeric values.
Premium fields must be numeric: basicOd, ncbDiscount, netOd, basicTp, netTp, taxes, total.
If registration date or manufacturing date is present, extract registrationYear/manufactureYear as an integer.
For geography, extract the exact printed RTO code (e.g. 'UP-16', 'DL 9C', 'HR-26') and the exact printed location/address text.
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
        
        # Prepare page images at 150 DPI across all pages (up to 30 pages)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_parts = []
        
        total_pages = len(doc)
        if total_pages > 30:
            raise ValueError(
                f"Policy document exceeds maximum supported limit of 30 pages (received {total_pages} pages). "
                f"To maintain deterministic compliance, documents over 30 pages cannot be processed in a single run without batch splitting."
            )
            
        pages_to_extract = list(range(total_pages))
        logger.info(f"Extracting facts for {file_name}: rendering {total_pages} pages at 150 DPI for Gemini extraction.")
        
        for page_idx in pages_to_extract:
            pix = doc[page_idx].get_pixmap(dpi=150)
            img_bytes = pix.tobytes("jpeg")
            page_parts.append(types.Part.from_bytes(
                data=img_bytes,
                mime_type="image/jpeg"
            ))
            
        prompt = f"Analyze this entire motor policy document ({file_name}, total {total_pages} pages). Pages are 1-indexed (Page 1 through {total_pages}). Extract all rating facts following the schema strictly. Remember: if a field is not stated, value must be null."
        contents = [prompt] + page_parts
        
        # Call API with progressive backoff and fallback model if 503 spike occurs
        max_retries = 3
        candidate_models = [self.model]
        for m in [settings.GEMINI_FALLBACK_MODEL, "gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-1.5-flash"]:
            if m and m not in candidate_models:
                candidate_models.append(m)
        
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
                    
                    # Clean any accidental textual null strings like "not printed on policy", ":null", "null" to real JSON None
                    for key in ["insurer", "previousInsurer", "fuel", "make", "model", "rto", "printedLocation", "engineCc", "registrationYear", "policyStartDate"]:
                        if key in data and isinstance(data[key], dict):
                            val = data[key].get("value")
                            if isinstance(val, str) and (val.strip().lower() in ("null", ":null", "none", "unknown", "n/a", "not applicable") or "not printed" in val.lower()):
                                if not data[key].get("uncertainty"):
                                    data[key]["uncertainty"] = val
                                data[key]["value"] = None
                                data[key]["lowConfidence"] = True
                    
                    # Derive vehicleAgeYears using age_helper
                    from backend.app.resolver.age_helper import calculate_vehicle_age
                    reg_year = data.get("registrationYear", {}).get("value") if data.get("registrationYear") else None
                    start_date = data.get("policyStartDate", {}).get("value", "") if data.get("policyStartDate") else None
                    age_val, age_expl = calculate_vehicle_age(start_date, reg_year)
                        
                    data["vehicleAgeYears"] = {
                        "value": age_val,
                        "page": data.get("registrationYear", {}).get("page") if data.get("registrationYear") else None,
                        "confidence": 0.95,
                        "uncertainty": age_expl
                    }
                    
                    # Business Type Rule (ITEM 4):
                    # If previousInsurer is null / missing / 'null', businessType = 'unknown', never rollover
                    prev_ins_obj = data.get("previousInsurer", {})
                    prev_ins_val = prev_ins_obj.get("value") if isinstance(prev_ins_obj, dict) else None
                    if not prev_ins_val or not str(prev_ins_val).strip() or str(prev_ins_val).lower() in ("null", "none", "not available", "unknown", "n/a"):
                        if "businessType" not in data or not data["businessType"]:
                            data["businessType"] = {}
                        data["businessType"]["value"] = "unknown"
                        data["businessType"]["uncertainty"] = "Previous insurer is null or not printed; business type set to unknown"
                    else:
                        curr_ins = (data.get("insurer", {}).get("value") or "").upper()
                        prev_ins = str(prev_ins_val).upper()
                        if any(w in curr_ins for w in prev_ins.split() if len(w) > 3):
                            data["businessType"]["value"] = "renewal"
                        else:
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
