import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import asyncio
import argparse
from backend.app.grids.registry import registry
from backend.app.resolver.resolver import resolve_policy
from backend.app.resolver.states import PolicyFacts
from backend.app.extraction.gemini_extractor import GeminiFactExtractor

BENCHMARK_POLICIES = [
    {
        "insurer_slug": "hdfc_ergo",
        "output_file": "outputs/hdfc-ergo.json",
        "pdf_path": "sample-policies/pvt-car-comprehensive-hdfc-ergo.pdf"
    },
    {
        "insurer_slug": "reliance",
        "output_file": "outputs/reliance.json",
        "pdf_path": "sample-policies/pvt-car-comprehensive-reliance.pdf"
    },
    {
        "insurer_slug": "godigit",
        "output_file": "outputs/godigit.json",
        "pdf_path": "sample-policies/pvt-car-satp-go-digit.pdf"
    },
    {
        "insurer_slug": "tata_aig",
        "output_file": "outputs/tata-aig.json",
        "pdf_path": "sample-policies/pvt-car-satp-tata-aig.pdf"
    }
]

async def run_live_extraction():
    extractor = GeminiFactExtractor()
    if not extractor.api_key:
        print("ERROR: GEMINI_API_KEY is not configured in rater/.env.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Running live extraction with model: {extractor.model}...")
    for item in BENCHMARK_POLICIES:
        pdf_path = os.path.join(os.path.dirname(__file__), "..", item["pdf_path"])
        print(f"\nProcessing {item['insurer_slug']} from {item['pdf_path']}...")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
            
        try:
            extraction = await extractor.extract_facts(pdf_bytes, os.path.basename(pdf_path))
            facts: PolicyFacts = extraction["facts"]
            grid = registry.get_grid(item["insurer_slug"])
            resolution = resolve_policy(facts, grid)
            
            output_data = {
                "id": f"live-{item['insurer_slug']}",
                "fileName": os.path.basename(pdf_path),
                "status": resolution.status.value,
                "rates": {k: v.model_dump() for k, v in resolution.rates.items()},
                "confidence": resolution.confidence,
                "facts": facts.model_dump(),
                "trace": [t.model_dump() for t in resolution.trace]
            }
            
            out_path = os.path.join(os.path.dirname(__file__), "..", item["output_file"])
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)
            print(f"Wrote live output to {item['output_file']} (Status: {resolution.status.value})")
        except Exception as e:
            print(f"Live extraction failed for {item['insurer_slug']}: {e}", file=sys.stderr)
            print("Keeping verified benchmark output in place.")
        
        # Friendly delay between live API calls
        await asyncio.sleep(4)

def main():
    parser = argparse.ArgumentParser(description="Generate benchmark outputs")
    parser.add_argument("--live", action="store_true", help="Run live Gemini extraction on sample PDFs")
    args = parser.parse_args()
    
    if args.live:
        asyncio.run(run_live_extraction())
    else:
        print("Outputs already initialized from verified facts.")

if __name__ == "__main__":
    main()
