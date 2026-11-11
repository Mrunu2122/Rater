import pytest
from backend.app.grids.registry import registry
from backend.app.resolver.resolver import resolve_policy
from backend.app.resolver.states import (
    PolicyFacts, FactField, PremiumBreakup, ComponentState, RunStatus
)

def test_hdfc_ergo_golden():
    facts = PolicyFacts(
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
    
    grid = registry.get_grid("hdfc_ergo")
    assert grid is not None
    res = resolve_policy(facts, grid)
    
    assert res.status == RunStatus.RESOLVED
    assert res.rates["od"].applicable is True
    assert res.rates["od"].state == ComponentState.RESOLVED
    assert res.rates["od"].ratePercent == 15.0 # Zone 2 Table, Row 5 (<10k), Col 3 (Package, Non-Petrol, NCB)
    assert res.rates["tp"].state == ComponentState.UNSUPPORTED # TP not published in HDFC schedule
    assert len(res.trace) >= 4

def test_hdfc_ergo_exact_slab_boundary():
    # Test boundary check at exactly 10,000.0 Net OD
    facts = PolicyFacts(
        insurer=FactField(value="HDFC ERGO", page=1),
        previousInsurer=FactField(value="TATA AIG", page=1),
        businessType=FactField(value="rollover", page=1),
        policyType=FactField(value="comprehensive", page=1),
        make=FactField(value="MAHINDRA", page=1),
        model=FactField(value="BOLERO", page=1),
        fuel=FactField(value="diesel", page=1),
        rto=FactField(value="HR-26", page=1),
        printedLocation=FactField(value="HARYANA", page=1),
        premiums=PremiumBreakup(netOd=10000.0, page=1)
    )
    grid = registry.get_grid("hdfc_ergo")
    res = resolve_policy(facts, grid)
    assert res.status == RunStatus.AMBIGUOUS
    assert res.rates["od"].state == ComponentState.AMBIGUOUS
    assert "undefined grid slab boundary" in res.rates["od"].reason

def test_reliance_golden():
    facts = PolicyFacts(
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
    
    grid = registry.get_grid("reliance")
    assert grid is not None
    res = resolve_policy(facts, grid)
    
    assert res.status == RunStatus.RESOLVED
    assert res.rates["od"].applicable is True
    assert res.rates["od"].state == ComponentState.RESOLVED
    # Base rate 22.5% minus 5.0% = 17.5%
    assert res.rates["od"].ratePercent == 17.5
    # TP strictly not published per H2
    assert res.rates["tp"].state == ComponentState.UNSUPPORTED
    assert "H2" in res.rates["tp"].citations[0]["coordinate"]

def test_godigit_golden():
    facts = PolicyFacts(
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
    
    grid = registry.get_grid("godigit")
    assert grid is not None
    res = resolve_policy(facts, grid)
    
    assert res.status == RunStatus.RESOLVED
    assert res.rates["od"].applicable is False
    assert res.rates["od"].state == ComponentState.NOT_APPLICABLE
    assert res.rates["tp"].applicable is True
    assert res.rates["tp"].state == ComponentState.RESOLVED
    assert res.rates["tp"].ratePercent == 29.5 # 4W SATP Row 293 (UP_Bad, Petrol>1000, Age All)

def test_tata_aig_golden():
    facts = PolicyFacts(
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
    
    grid = registry.get_grid("tata_aig")
    assert grid is not None
    res = resolve_policy(facts, grid)
    
    # Grounded refusal: status unsupported, candidate base rate 38% reported in trace
    assert res.status == RunStatus.UNSUPPORTED
    assert res.rates["od"].applicable is False
    assert res.rates["od"].state == ComponentState.NOT_APPLICABLE
    assert res.rates["tp"].applicable is True
    assert res.rates["tp"].state == ComponentState.UNSUPPORTED
    assert res.rates["tp"].ratePercent is None
    assert "base commission only" in res.rates["tp"].reason
    assert any("Refused final TP rate with proof" in t.decision for t in res.trace)
    assert any("Pvtcar!F3" in str(t.gridCitation) for t in res.trace)
