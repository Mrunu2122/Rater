import os
import json
import glob
from backend.app.grids.registry import registry
from backend.app.resolver.resolver import resolve_policy
from backend.app.resolver.states import PolicyFacts, FactField, PremiumBreakup

os.makedirs("outputs", exist_ok=True)

policies = [
    {
        "id": "hdfc-ergo",
        "file": "pvt-car-comprehensive-hdfc-ergo.pdf",
        "grid_id": "hdfc_ergo",
        "facts": PolicyFacts(
            insurer=FactField(value="HDFC ERGO General Insurance Company Limited", page=1, confidence=0.99),
            previousInsurer=FactField(value="TATA AIG GENERAL INSURANCE CO.LTD.", page=1, confidence=0.95),
            businessType=FactField(value="rollover", page=1, confidence=0.95),
            policyType=FactField(value="comprehensive", page=1, confidence=0.98),
            make=FactField(value="MAHINDRA", page=1),
            model=FactField(value="BOLERO NEO-N10 (R)", page=1),
            fuel=FactField(value="diesel", page=1, lowConfidence=True, uncertainty="Fuel type not printed on policy schedule; inferred from model Mahindra Bolero Neo 1493cc"),
            rto=FactField(value="HR-26", page=1),
            printedLocation=FactField(value="HARYANA 122002 GURUGRAM GURGAON", page=1),
            engineCc=FactField(value=1493, page=1),
            registrationYear=FactField(value=2023, page=1),
            vehicleAgeYears=FactField(value=3, page=1),
            policyStartDate=FactField(value="2026-03-29", page=1),
            premiums=PremiumBreakup(
                basicOd=2433.0,
                ncbDiscount=852.0,
                netOd=8053.0,
                basicTp=3416.0,
                netTp=3816.0,
                taxes=2136.0,
                total=14005.0,
                page=1,
                ncbPercent=35.0
            )
        )
    },
    {
        "id": "reliance",
        "file": "pvt-car-comprehensive-reliance.pdf",
        "grid_id": "reliance",
        "facts": PolicyFacts(
            insurer=FactField(value="Reliance General Insurance Company Limited", page=2),
            previousInsurer=FactField(value=None, page=2, lowConfidence=True, uncertainty="Previous insurer not stated on schedule"),
            businessType=FactField(value="unknown", page=2, lowConfidence=True, uncertainty="Previous insurer not stated"),
            policyType=FactField(value="comprehensive", page=2),
            make=FactField(value="RENAULT", page=2),
            model=FactField(value="KWID 1.0 RXT O", page=2),
            fuel=FactField(value="petrol", page=2),
            rto=FactField(value="UP-16", page=2),
            printedLocation=FactField(value="UTTAR PRADESH - Noida DADRI GAUTAM BUDDHA NAGAR", page=2),
            engineCc=FactField(value=999, page=2),
            registrationYear=FactField(value=2020, page=2),
            vehicleAgeYears=FactField(value=5, page=2),
            policyStartDate=FactField(value="2025-12-23", page=2),
            premiums=PremiumBreakup(
                basicOd=5064.16,
                ncbDiscount=350.01,
                netOd=4714.00,
                basicTp=2094.00,
                netTp=2519.00,
                taxes=1302.00,
                total=8535.00,
                page=2,
                ncbPercent=25.0,
                ncbUnclearNote="NCB base unclear: 25% of 5064.16 is 1266.04; 350.01 implies base 1400.04"
            )
        )
    },
    {
        "id": "godigit",
        "file": "pvt-car-satp-go-digit.pdf",
        "grid_id": "godigit",
        "facts": PolicyFacts(
            insurer=FactField(value="Go Digit General Insurance Ltd.", page=1),
            previousInsurer=FactField(value="Go Digit General Insurance Limited", page=2),
            businessType=FactField(value="renewal", page=2),
            policyType=FactField(value="stand_alone_tp", page=1),
            make=FactField(value="HYUNDAI", page=1),
            model=FactField(value="SANTRO NEW/1.1MT CORPORATE", page=1),
            fuel=FactField(value="petrol", page=1),
            rto=FactField(value="UP-78", page=1),
            printedLocation=FactField(value="Kanpur Nagar, UTTAR PRADESH", page=1),
            engineCc=FactField(value=1086, page=1),
            registrationYear=FactField(value=2019, page=1),
            manufactureYear=FactField(value=None, page=1, lowConfidence=True, uncertainty="0001-01-01 unpopulated"),
            vehicleAgeYears=FactField(value=7, page=1),
            policyStartDate=FactField(value="2026-03-25", page=1),
            premiums=PremiumBreakup(
                basicTp=3416.0,
                netTp=3466.0,
                taxes=623.88,
                total=4089.88,
                page=2
            )
        )
    },
    {
        "id": "tata-aig",
        "file": "pvt-car-satp-tata-aig.pdf",
        "grid_id": "tata_aig",
        "facts": PolicyFacts(
            insurer=FactField(value="TATA AIG GENERAL INSURANCE COMPANY LIMITED", page=1),
            previousInsurer=FactField(value="TATA AIG GENERAL INSURANCE CO.LTD.", page=11),
            businessType=FactField(value="renewal", page=11),
            policyType=FactField(value="stand_alone_tp", page=1),
            make=FactField(value="MARUTI", page=4),
            model=FactField(value="ZEN ESTILO / LXI CNG / HATCH BACK", page=4),
            fuel=FactField(value="cng", page=4),
            rto=FactField(value="DL 9C AB 2893", page=4),
            printedLocation=FactField(value="New Delhi, DELHI-DELHI, 110059, DELHI, India", page=1),
            engineCc=FactField(value=998, page=4),
            registrationYear=FactField(value=2011, page=4),
            vehicleAgeYears=FactField(value=15, page=4),
            policyStartDate=FactField(value="2026-04-01", page=1),
            premiums=PremiumBreakup(
                basicTp=2094.0,
                netTp=2154.0,
                taxes=388.0,
                total=2542.0,
                page=5
            )
        )
    }
]

print("Generating outputs for all 4 benchmark policies...")
for p in policies:
    grid = registry.get_grid(p["grid_id"])
    res = resolve_policy(p["facts"], grid)
    out_obj = {
        "policyFile": p["file"],
        "status": res.status.value,
        "confidence": res.confidence,
        "facts": p["facts"].model_dump(),
        "rates": {k: v.model_dump() for k, v in res.rates.items()},
        "trace": [t.model_dump() for t in res.trace],
        "appliedGridChecksum": res.appliedGridChecksum,
        "resolverVersion": res.resolverVersion
    }
    out_path = os.path.join("outputs", f"{p['id']}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, indent=2)
    print(f"  [SAVED] {out_path} -> status: {res.status.value}")

print("Done generating outputs.")
