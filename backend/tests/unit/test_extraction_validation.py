import pytest
from unittest.mock import MagicMock, patch
from backend.app.extraction.gemini_extractor import GeminiFactExtractor

@pytest.mark.anyio
async def test_extractor_mocked_gemini():
    fake_gemini_json = """
    {
      "insurer": {"value": "Go Digit General Insurance Ltd.", "page": 1, "confidence": 0.99},
      "previousInsurer": {"value": "Go Digit", "page": 2, "confidence": 0.95},
      "businessType": {"value": "renewal", "page": 2, "confidence": 0.95},
      "policyType": {"value": "stand_alone_tp", "page": 1, "confidence": 0.98},
      "make": {"value": "HYUNDAI", "page": 1, "confidence": 0.95},
      "model": {"value": "SANTRO", "page": 1, "confidence": 0.95},
      "fuel": {"value": "petrol", "page": 1, "confidence": 0.95},
      "rto": {"value": "UP-78", "page": 1, "confidence": 0.95},
      "printedLocation": {"value": "Kanpur Nagar", "page": 1, "confidence": 0.95},
      "engineCc": {"value": 1086, "page": 1, "confidence": 0.95},
      "registrationYear": {"value": 2019, "page": 1, "confidence": 0.95},
      "vehicleAgeYears": {"value": 7, "page": 1, "confidence": 0.95},
      "policyStartDate": {"value": "2026-03-25", "page": 1, "confidence": 0.95},
      "premiums": {
        "netTp": 3466.0,
        "total": 4089.88,
        "page": 2,
        "confidence": 0.98
      }
    }
    """
    
    extractor = GeminiFactExtractor(api_key="mock-key-for-test")
    
    mock_response = MagicMock()
    mock_response.text = fake_gemini_json
    
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    
    with patch("google.genai.Client", return_value=mock_client):
        # Create a tiny 1-page valid PDF
        import fitz
        doc = fitz.open()
        doc.new_page()
        pdf_bytes = doc.tobytes()
        
        res = await extractor.extract_facts(pdf_bytes, "sample.pdf")
        assert res["facts"].insurer.value == "Go Digit General Insurance Ltd."
        assert res["facts"].engineCc.value == 1086
        assert res["facts"].premiums.netTp == 3466.0
        assert res["model_id"] == "gemini-3.5-flash"
