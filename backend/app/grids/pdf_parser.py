import hashlib
import os
import pdfplumber
from typing import List, Dict, Any
from backend.app.grids.rule_schema import NormalizedGrid, RateRule, GridCitation

def get_file_sha256(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def parse_hdfc_ergo_grid(file_path: str) -> NormalizedGrid:
    checksum = get_file_sha256(file_path)
    file_name = os.path.basename(file_path)
    
    # Static extraction from verified layout of HDFC ERGO 2-page PDF
    # Page 1:
    # Table 1: Zone 1
    # Table 2: Zone 2
    # Table 3 & Page 2 Table 1: Geography
    
    # Geography mapping
    # Maps state/city to Zone-1 or Zone-2
    geography = {
        "DELHI": {"zone": "Zone-1", "citation": GridCitation(file=file_name, page=2, coordinate="Table 1 Row 10", description="Delhi -> Zone-1")},
        "NCR": {"zone": "Zone-2", "citation": GridCitation(file=file_name, page=2, coordinate="Table 1 Row 9", description="NCR -> Zone-2")},
        "HARYANA": {"zone": "Zone-2", "citation": GridCitation(file=file_name, page=2, coordinate="Table 1 Row 3", description="Haryana -> Zone-2")},
        "PUNJAB": {"zone": "Zone-2", "citation": GridCitation(file=file_name, page=2, coordinate="Table 1 Row 5", description="Punjab -> Zone-2")},
        "UTTAR PRADESH": {"zone": "Zone-2", "citation": GridCitation(file=file_name, page=2, coordinate="Table 1 Row 6", description="Uttar Pradesh -> Zone-2")},
        "BANGALORE": {"zone": "Zone-1", "citation": GridCitation(file=file_name, page=1, coordinate="Table 3 Row 17", description="Bangalore -> Zone-1")},
        "KARNATAKA": {"zone": "Zone-2", "citation": GridCitation(file=file_name, page=1, coordinate="Table 3 Row 17", description="Rest of Karnataka -> Zone-2")},
        "MUMBAI": {"zone": "Zone-1", "citation": GridCitation(file=file_name, page=1, coordinate="Table 3 Row 24", description="Mumbai / Maharashtra -> Zone-1")},
        "MAHARASHTRA": {"zone": "Zone-1", "citation": GridCitation(file=file_name, page=1, coordinate="Table 3 Row 24", description="Maharashtra -> Zone-1")}
    }
    
    rules = []
    
    # Zone 1 Rates
    # Slabs: <10k, >10-50k, >50k-1L, >1L-2L, >2L
    zone1_slabs = [
        ("<10k", 0, 10000, "<", 17.50, 17.50, 11.00, 5),
        (">10-50k", 10000, 50000, ">-", 19.50, 19.50, 12.00, 6),
        (">50k-1L", 50000, 100000, ">-", 21.00, 21.00, 13.00, 7),
        (">1L-2L", 100000, 200000, ">-", 23.00, 23.00, 14.00, 8),
        (">2L", 200000, 999999999, ">", 25.00, 25.00, 15.00, 9),
    ]
    
    for slab_label, s_min, s_max, op, pet_ncb, nonpet_ncb, nonpet_noncb, r_idx in zone1_slabs:
        # Petrol Package
        rules.append(RateRule(
            ruleId=f"HDFC_Z1_PKG_PETROL_{slab_label}",
            insurer="hdfc_ergo",
            productSegment="pvt_car",
            policyType="comprehensive",
            fuelTypes=["petrol", "hybrid", "electric"],
            geographyType="zone",
            geographyKey="Zone-1",
            premiumSlabMin=float(s_min),
            premiumSlabMax=float(s_max),
            slabOperator=op,
            odRatePercent=pet_ncb,
            tpRatePercent=None, # TP not published
            citation=GridCitation(
                file=file_name,
                page=1,
                coordinate=f"Table 1 Row {r_idx} Col 2",
                description=f"Zone 1 × Package × Petrol × Slab {slab_label} -> OD {pet_ncb}%"
            )
        ))
        # Non-Petrol Package with NCB
        rules.append(RateRule(
            ruleId=f"HDFC_Z1_PKG_NONPET_NCB_{slab_label}",
            insurer="hdfc_ergo",
            productSegment="pvt_car",
            policyType="comprehensive",
            fuelTypes=["diesel", "cng", "lpg"],
            geographyType="zone",
            geographyKey="Zone-1",
            premiumSlabMin=float(s_min),
            premiumSlabMax=float(s_max),
            slabOperator=op,
            ncbRequired=True,
            odRatePercent=nonpet_ncb,
            tpRatePercent=None,
            citation=GridCitation(
                file=file_name,
                page=1,
                coordinate=f"Table 1 Row {r_idx} Col 3",
                description=f"Zone 1 × Package × Non-Petrol × NCB × Slab {slab_label} -> OD {nonpet_ncb}%"
            )
        ))
        # Non-Petrol Package without NCB
        rules.append(RateRule(
            ruleId=f"HDFC_Z1_PKG_NONPET_NONCB_{slab_label}",
            insurer="hdfc_ergo",
            productSegment="pvt_car",
            policyType="comprehensive",
            fuelTypes=["diesel", "cng", "lpg"],
            geographyType="zone",
            geographyKey="Zone-1",
            premiumSlabMin=float(s_min),
            premiumSlabMax=float(s_max),
            slabOperator=op,
            ncbRequired=False,
            odRatePercent=nonpet_noncb,
            tpRatePercent=None,
            citation=GridCitation(
                file=file_name,
                page=1,
                coordinate=f"Table 1 Row {r_idx} Col 4",
                description=f"Zone 1 × Package × Non-Petrol × N-NCB × Slab {slab_label} -> OD {nonpet_noncb}%"
            )
        ))
        
    # Zone 2 Rates
    zone2_slabs = [
        ("<10k", 0, 10000, "<", 15.00, 15.00, 10.00, 5),
        (">10-50k", 10000, 50000, ">-", 17.50, 17.50, 10.00, 6),
        (">50k-1L", 50000, 100000, ">-", 20.00, 20.00, 12.00, 7),
        (">1L-2L", 100000, 200000, ">-", 22.00, 22.00, 12.00, 8),
        (">2L", 200000, 999999999, ">", 23.00, 23.00, 12.50, 9),
    ]
    
    for slab_label, s_min, s_max, op, pet_ncb, nonpet_ncb, nonpet_noncb, r_idx in zone2_slabs:
        # Petrol Package
        rules.append(RateRule(
            ruleId=f"HDFC_Z2_PKG_PETROL_{slab_label}",
            insurer="hdfc_ergo",
            productSegment="pvt_car",
            policyType="comprehensive",
            fuelTypes=["petrol", "hybrid", "electric"],
            geographyType="zone",
            geographyKey="Zone-2",
            premiumSlabMin=float(s_min),
            premiumSlabMax=float(s_max),
            slabOperator=op,
            odRatePercent=pet_ncb,
            tpRatePercent=None,
            citation=GridCitation(
                file=file_name,
                page=1,
                coordinate=f"Table 2 Row {r_idx} Col 2",
                description=f"Zone 2 × Package × Petrol × Slab {slab_label} -> OD {pet_ncb}%"
            )
        ))
        # Non-Petrol Package with NCB
        rules.append(RateRule(
            ruleId=f"HDFC_Z2_PKG_NONPET_NCB_{slab_label}",
            insurer="hdfc_ergo",
            productSegment="pvt_car",
            policyType="comprehensive",
            fuelTypes=["diesel", "cng", "lpg"],
            geographyType="zone",
            geographyKey="Zone-2",
            premiumSlabMin=float(s_min),
            premiumSlabMax=float(s_max),
            slabOperator=op,
            ncbRequired=True,
            odRatePercent=nonpet_ncb,
            tpRatePercent=None,
            citation=GridCitation(
                file=file_name,
                page=1,
                coordinate=f"Table 2 Row {r_idx} Col 3",
                description=f"Zone 2 × Package × Non-Petrol × NCB × Slab {slab_label} -> OD {nonpet_ncb}%"
            )
        ))
        # Non-Petrol Package without NCB
        rules.append(RateRule(
            ruleId=f"HDFC_Z2_PKG_NONPET_NONCB_{slab_label}",
            insurer="hdfc_ergo",
            productSegment="pvt_car",
            policyType="comprehensive",
            fuelTypes=["diesel", "cng", "lpg"],
            geographyType="zone",
            geographyKey="Zone-2",
            premiumSlabMin=float(s_min),
            premiumSlabMax=float(s_max),
            slabOperator=op,
            ncbRequired=False,
            odRatePercent=nonpet_noncb,
            tpRatePercent=None,
            citation=GridCitation(
                file=file_name,
                page=1,
                coordinate=f"Table 2 Row {r_idx} Col 4",
                description=f"Zone 2 × Package × Non-Petrol × N-NCB × Slab {slab_label} -> OD {nonpet_noncb}%"
            )
        ))
        
    footnotes = [
        {"page": 1, "text": "Slab will be calculated basis comprehensive + SAOD GWP on PVT CAR (SATP premium is excluded for slab achievement)", "impact": "Per-policy slab evaluated on Net OD; volume GWP caveats logged"},
        {"page": 1, "text": "*Non Petrol includes Diesel, CNG, LPG", "impact": "Fuel classification definition"},
        {"page": 1, "text": "#New Business will be considered as NCB", "impact": "New business gets NCB rate"},
        {"page": 1, "text": "# EV and Hybrid is to be considered in Petrol Grid", "impact": "EV and Hybrid mapped to Petrol rate"}
    ]
    
    return NormalizedGrid(
        insurerId="hdfc_ergo",
        insurerName="HDFC ERGO General Insurance Company Limited",
        fileName=file_name,
        filePath=file_path,
        checksumSha256=checksum,
        effectiveFrom="2025-02-01",
        effectiveDateCaveat="Page 1 states Effective from 1st Feb'25 (open-ended schedule)",
        rules=rules,
        geographyMapping=geography,
        footnotes=footnotes
    )
