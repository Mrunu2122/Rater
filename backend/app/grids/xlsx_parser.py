import hashlib
import os
import openpyxl
from typing import List, Dict, Any, Optional
from backend.app.grids.rule_schema import NormalizedGrid, RateRule, GridCitation

def get_file_sha256(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def parse_godigit_grid(file_path: str) -> NormalizedGrid:
    checksum = get_file_sha256(file_path)
    file_name = os.path.basename(file_path)
    wb = openpyxl.load_workbook(file_path, data_only=True)
    
    # 1. Parse Geography (4W  RTO)
    ws_rto = wb["4W  RTO"]
    rto_mapping = {}
    for r in range(3, ws_rto.max_row + 1):
        rto_code = ws_rto.cell(r, 2).value
        tp_cluster = ws_rto.cell(r, 3).value
        package_cluster = ws_rto.cell(r, 4).value
        saod_cluster = ws_rto.cell(r, 5).value
        plr_cluster = ws_rto.cell(r, 6).value
        if rto_code:
            norm_code = str(rto_code).strip().replace("-", "").upper()
            rto_mapping[norm_code] = {
                "raw_rto": str(rto_code).strip(),
                "4WTP": str(tp_cluster).strip() if tp_cluster else None,
                "4W_Package": str(package_cluster).strip() if package_cluster else None,
                "4W_SAOD": str(saod_cluster).strip() if saod_cluster else None,
                "citation": GridCitation(
                    file=file_name,
                    sheet="4W  RTO",
                    coordinate=f"B{r}:F{r}",
                    description=f"RTO {rto_code} maps to 4WTP cluster {tp_cluster}"
                )
            }
            
    # 2. Parse 4W SATP Rates
    ws_satp = wb["4W SATP"]
    rules = []
    for r in range(3, ws_satp.max_row + 1):
        cluster = ws_satp.cell(r, 2).value
        segment = ws_satp.cell(r, 3).value
        age_str = ws_satp.cell(r, 4).value
        cd2_val = ws_satp.cell(r, 5).value
        note = ws_satp.cell(r, 6).value
        
        if not cluster or not segment or cd2_val is None:
            continue
            
        cluster_str = str(cluster).strip()
        segment_str = str(segment).strip()
        
        # Parse fuel and CC from segment
        # Examples: Petrol<1000, Petrol>1000, Diesel<1500, Diesel>1500, CNG, CNG<1000, CNG>1000
        fuel_types = []
        cc_min = None
        cc_max = None
        
        if "PETROL" in segment_str.upper():
            fuel_types.append("petrol")
        if "DIESEL" in segment_str.upper():
            fuel_types.append("diesel")
        if "CNG" in segment_str.upper():
            fuel_types.append("cng")
            
        if "<1000" in segment_str:
            cc_max = 1000.0
        elif ">1000" in segment_str:
            cc_min = 1000.0
        elif "<1500" in segment_str:
            cc_max = 1500.0
        elif ">1500" in segment_str:
            cc_min = 1500.0
            
        # Parse age
        age_min = None
        age_max = None
        age_clean = str(age_str).strip() if age_str else "All"
        if "<10" in age_clean:
            age_max = 10.0
        elif ">10" in age_clean:
            age_min = 10.0
            
        tp_percent = float(cd2_val) * 100.0
        
        rule = RateRule(
            ruleId=f"GODIGIT_SATP_R{r}",
            insurer="godigit",
            productSegment="pvt_car",
            policyType="stand_alone_tp",
            fuelTypes=fuel_types,
            geographyType="cluster",
            geographyKey=cluster_str,
            ccMin=cc_min,
            ccMax=cc_max,
            vehicleAgeMin=age_min,
            vehicleAgeMax=age_max,
            tpRatePercent=tp_percent,
            citation=GridCitation(
                file=file_name,
                sheet="4W SATP",
                coordinate=f"B{r}:E{r}",
                description=f"Cluster {cluster_str} × {segment_str} × Age {age_clean} -> Max CD2 = {cd2_val} ({tp_percent}%)"
            ),
            notes=str(note).strip() if note else None
        )
        rules.append(rule)
        
    return NormalizedGrid(
        insurerId="godigit",
        insurerName="Go Digit General Insurance Ltd.",
        fileName=file_name,
        filePath=file_path,
        checksumSha256=checksum,
        effectiveFrom="2026-03-01",
        effectiveDateCaveat="Effective date inferred from folder march-2026 and sheet header Digit_FY 25-26",
        rules=rules,
        geographyMapping=rto_mapping,
        footnotes=[]
    )

def parse_reliance_grid(file_path: str) -> NormalizedGrid:
    checksum = get_file_sha256(file_path)
    file_name = os.path.basename(file_path)
    wb = openpyxl.load_workbook(file_path, data_only=True)
    
    # 1. Parse Geography (RTO List)
    ws_rto = wb["RTO List"]
    rto_mapping = {}
    for r in range(2, ws_rto.max_row + 1):
        reg_code = ws_rto.cell(r, 1).value
        col1 = ws_rto.cell(r, 2).value
        reg_city = ws_rto.cell(r, 3).value
        zone = ws_rto.cell(r, 5).value
        if reg_code:
            norm_code = str(reg_code).strip().replace("-", "").upper()
            rto_mapping[norm_code] = {
                "raw_rto": str(reg_code).strip(),
                "city": str(reg_city).strip() if reg_city else None,
                "zone": str(zone).strip() if zone else None,
                "citation": GridCitation(
                    file=file_name,
                    sheet="RTO List",
                    coordinate=f"A{r}:E{r}",
                    description=f"RTO {reg_code} maps to Region_City: {reg_city}, Zone: {zone}"
                )
            }
            
    # 2. Parse PRIVATE CAR COMP, SAOD & STP
    ws_car = wb["PRIVATE CAR COMP, SAOD & STP"]
    rules = []
    current_zone = None
    
    for r in range(3, 18):
        zone_val = ws_car.cell(r, 1).value
        if zone_val:
            current_zone = str(zone_val).strip()
            
        rto_region = ws_car.cell(r, 2).value
        petrol_comp = ws_car.cell(r, 3).value
        diesel_comp = ws_car.cell(r, 4).value
        saod = ws_car.cell(r, 5).value
        stp = ws_car.cell(r, 6).value
        
        if not rto_region:
            continue
            
        region_str = str(rto_region).strip()
        
        # Petrol / Bifuel Comprehensive
        if petrol_comp is not None:
            rules.append(RateRule(
                ruleId=f"RELIANCE_COMP_PETROL_R{r}",
                insurer="reliance",
                productSegment="pvt_car",
                policyType="comprehensive",
                fuelTypes=["petrol", "cng", "lpg"],
                geographyType="rto_region",
                geographyKey=region_str,
                odRatePercent=float(petrol_comp),
                tpRatePercent=None, # TP not published in this grid per H2
                citation=GridCitation(
                    file=file_name,
                    sheet="PRIVATE CAR COMP, SAOD & STP",
                    coordinate=f"A{r}:C{r}",
                    description=f"Zone {current_zone} × Region {region_str} × Petrol/Bifuel/Comp -> OD {petrol_comp}%"
                )
            ))
            
        # Diesel / EV Comprehensive
        if diesel_comp is not None:
            rules.append(RateRule(
                ruleId=f"RELIANCE_COMP_DIESEL_R{r}",
                insurer="reliance",
                productSegment="pvt_car",
                policyType="comprehensive",
                fuelTypes=["diesel", "electric"],
                geographyType="rto_region",
                geographyKey=region_str,
                odRatePercent=float(diesel_comp),
                tpRatePercent=None,
                citation=GridCitation(
                    file=file_name,
                    sheet="PRIVATE CAR COMP, SAOD & STP",
                    coordinate=f"A{r}:D{r}",
                    description=f"Zone {current_zone} × Region {region_str} × Diesel/EV/Comp -> OD {diesel_comp}%"
                )
            ))
            
    footnotes = [
        {"cell": "H2", "text": "payout will made on OD Premium", "impact": "TP commission is not published / not payable for Comprehensive policies"},
        {"cell": "H3", "text": "Payout for < 1000 CC, PO will be 5% lesser than the above Grid", "impact": "For engine < 1000 CC, reduces payout by 5% points (assumption) or 5% relative"},
        {"cell": "H4", "text": "Standlone ZD policies 2.5%will be redused from the above Grid", "impact": "Zero Dep standalone deduction"},
        {"cell": "H5", "text": "EW of Pvivate car will be Flat 20% Payout", "impact": "Extended warranty"},
        {"cell": "H6", "text": "Addon Bundle (Tyre / RTI) if Sourced, 2.5% Additional Payout Shall be offered", "impact": "Addon bundle incentive"}
    ]
    
    return NormalizedGrid(
        insurerId="reliance",
        insurerName="Reliance General Insurance Company Limited",
        fileName=file_name,
        filePath=file_path,
        checksumSha256=checksum,
        effectiveFrom="2026-02-01",
        effectiveDateCaveat="Title states FEB 26 Grid, sheet header A1 states Jan-26; policy dated 2025-12-23 (warning logged)",
        rules=rules,
        geographyMapping=rto_mapping,
        footnotes=footnotes
    )

def parse_tata_aig_grid(file_path: str) -> NormalizedGrid:
    checksum = get_file_sha256(file_path)
    file_name = os.path.basename(file_path)
    wb = openpyxl.load_workbook(file_path, data_only=True)
    
    ws_pvt = wb["Pvtcar"]
    rules = []
    
    # 55 city/cluster columns from Col M (13) to Col BO (67)
    city_cols = {}
    for c in range(13, 68):
        cname = ws_pvt.cell(5, c).value
        if cname:
            city_cols[str(cname).strip().upper()] = (c, openpyxl.utils.get_column_letter(c), str(cname).strip())
            
    for r in range(6, ws_pvt.max_row + 1):
        v_type = ws_pvt.cell(r, 7).value
        b_type = ws_pvt.cell(r, 8).value
        f_type = ws_pvt.cell(r, 9).value
        sec_text = ws_pvt.cell(r, 10).value
        ncb = ws_pvt.cell(r, 11).value
        addon = ws_pvt.cell(r, 12).value
        
        if not sec_text:
            continue
            
        pol_type = "comprehensive" if "PACKAGE" in str(sec_text).upper() else ("stand_alone_tp" if "SATP" in str(sec_text).upper() else "stand_alone_od")
        fuel_clean = [str(f_type).strip().lower()] if f_type else ["all"]
        bzi_clean = str(b_type).strip().lower() if b_type else "all"
        
        # Read city rates
        for city_norm, (col_idx, col_letter, city_orig) in city_cols.items():
            rate_val = ws_pvt.cell(r, col_idx).value
            if rate_val is not None and isinstance(rate_val, (int, float)):
                rate_pct = float(rate_val) * 100.0
                rules.append(RateRule(
                    ruleId=f"TATA_PVTCAR_R{r}_{col_letter}",
                    insurer="tata_aig",
                    productSegment=str(v_type).strip() if v_type else "All",
                    policyType=pol_type,
                    fuelTypes=fuel_clean,
                    geographyType="city",
                    geographyKey=city_orig,
                    businessType=bzi_clean,
                    tpRatePercent=rate_pct if pol_type == "stand_alone_tp" else None,
                    odRatePercent=rate_pct if pol_type != "stand_alone_tp" else None,
                    citation=GridCitation(
                        file=file_name,
                        sheet="Pvtcar",
                        coordinate=f"G{r}:{col_letter}{r}",
                        description=f"Type {v_type} × {b_type} × {f_type} × {sec_text} × {city_orig} -> {rate_pct}%"
                    )
                ))
                
    return NormalizedGrid(
        insurerId="tata_aig",
        insurerName="Tata AIG General Insurance Company Limited",
        fileName=file_name,
        filePath=file_path,
        checksumSha256=checksum,
        effectiveFrom="2025-11-01",
        effectiveDateCaveat="Pvtcar Row 1 states applicable from 1st Nov'25 policies",
        rules=rules,
        geographyMapping={}, # No RTO table exists in workbook!
        footnotes=[
            {"sheet": "General Guidelines", "row": 5, "text": "Only Base Commission Needs to be updated in the Following sheet, Additionally we have created GWP based Rule Incremental COA"},
            {"sheet": "Pvtcar", "row": 3, "text": "***Below COA Rates would be Base Commission processed, Additionally GWP Based Rule will be Applicable"}
        ]
    )
