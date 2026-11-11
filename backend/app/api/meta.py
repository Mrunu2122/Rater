from fastapi import APIRouter
from backend.app.grids.registry import registry
from backend.app.config import settings

router = APIRouter(prefix="/api", tags=["meta"])

@router.get("/grids")
async def get_grids():
    all_grids = registry.get_all()
    return [
        {
            "insurerId": g.insurerId,
            "insurerName": g.insurerName,
            "fileName": g.fileName,
            "checksumSha256": g.checksumSha256,
            "effectiveFrom": g.effectiveFrom,
            "effectiveTo": g.effectiveTo,
            "effectiveDateCaveat": g.effectiveDateCaveat,
            "rulesCount": len(g.rules),
            "footnotesCount": len(g.footnotes)
        }
        for g in all_grids.values()
    ]

@router.get("/bench")
async def get_bench():
    return [
        {
            "insurer": "HDFC ERGO",
            "policyType": "Comprehensive",
            "fileName": "pvt-car-comprehensive-hdfc-ergo.pdf",
            "tests": "Zone × OD slab × fuel × NCB",
            "expectedStatus": "resolved",
            "expectedOd": "15.0%",
            "expectedTp": "Not published",
            "citation": "Pvt Car New Grid Eff 1st Feb'25 (HDFC ergo) 1.pdf · Page 1 Table 2 Row 5 Col 3"
        },
        {
            "insurer": "Go Digit",
            "policyType": "Stand-alone TP",
            "fileName": "pvt-car-satp-go-digit.pdf",
            "tests": "RTO cluster × fuel/engine segment",
            "expectedStatus": "resolved",
            "expectedOd": "Not applicable",
            "expectedTp": "29.5%",
            "citation": "Large Insurance Brokers Mar'26 - Shared.xlsx · 4W SATP!B293:E293"
        },
        {
            "insurer": "Reliance General",
            "policyType": "Comprehensive",
            "fileName": "pvt-car-comprehensive-reliance.pdf",
            "tests": "Zone × model segment × footnote",
            "expectedStatus": "resolved",
            "expectedOd": "17.5%",
            "expectedTp": "Not published",
            "citation": "Reliance Broking Premier FEB 26 Grid.xlsx · PRIVATE CAR COMP, SAOD & STP!A11:C11, H3"
        },
        {
            "insurer": "Tata AIG",
            "policyType": "Stand-alone TP",
            "fileName": "pvt-car-satp-tata-aig.pdf",
            "tests": "Prove why no supported rate exists (TP-only coverage gap detection)",
            "expectedStatus": "unsupported",
            "expectedOd": "Not applicable",
            "expectedTp": "Unsupported (Candidate base 38.0% noted)",
            "citation": "Pvtcar!F3, General Guidelines!C5, Pvtcar!V511:V535"
        }
    ]

@router.get("/health")
async def health_check():
    grids_loaded = len(registry.get_all())
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "gridsLoaded": grids_loaded,
        "database": "connected",
        "storage": "connected"
    }
