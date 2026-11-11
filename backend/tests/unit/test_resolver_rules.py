import pytest
from backend.app.grids.registry import registry
from backend.app.resolver.resolver import resolve_policy
from backend.app.resolver.states import (
    PolicyFacts, FactField, PremiumBreakup, ComponentState, RunStatus
)

def test_rule_tp_only_od_not_applicable():
    facts = PolicyFacts(
        insurer=FactField(value="Go Digit", page=1),
        previousInsurer=FactField(value="Go Digit", page=2),
        businessType=FactField(value="renewal", page=2),
        policyType=FactField(value="stand_alone_tp", page=1),
        make=FactField(value="HYUNDAI", page=1),
        model=FactField(value="SANTRO", page=1),
        fuel=FactField(value="petrol", page=1),
        rto=FactField(value="UP-78", page=1),
        printedLocation=FactField(value="Kanpur Nagar", page=1),
        engineCc=FactField(value=1086, page=1),
        vehicleAgeYears=FactField(value=5, page=1),
        premiums=PremiumBreakup(netTp=3466.0, page=1)
    )
    grid = registry.get_grid("godigit")
    res = resolve_policy(facts, grid)
    assert res.rates["od"].applicable is False
    assert res.rates["od"].state == ComponentState.NOT_APPLICABLE
    assert "Stand-alone TP policy" in res.rates["od"].reason

def test_rule_slab_boundary_ambiguous():
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
        premiums=PremiumBreakup(netOd=10000.0, page=1) # Exact 10k slab boundary
    )
    grid = registry.get_grid("hdfc_ergo")
    res = resolve_policy(facts, grid)
    assert res.status == RunStatus.AMBIGUOUS
    assert res.rates["od"].state == ComponentState.AMBIGUOUS
    assert "slab boundary" in res.rates["od"].reason

def test_rule_reliance_cc_footnote():
    # Kwid <1000 cc gets 5% lesser
    facts = PolicyFacts(
        insurer=FactField(value="Reliance General", page=1),
        previousInsurer=FactField(value=None, page=1),
        businessType=FactField(value="unknown", page=1),
        policyType=FactField(value="comprehensive", page=1),
        make=FactField(value="RENAULT", page=1),
        model=FactField(value="KWID", page=1),
        fuel=FactField(value="petrol", page=1),
        rto=FactField(value="UP-16", page=1),
        printedLocation=FactField(value="NOIDA GAUTAM BUDDHA NAGAR", page=1),
        engineCc=FactField(value=999, page=1),
        premiums=PremiumBreakup(netOd=4714.0, page=1)
    )
    grid = registry.get_grid("reliance")
    res = resolve_policy(facts, grid)
    assert res.rates["od"].ratePercent == 17.5 # 22.5% - 5.0%

def test_rule_reliance_tp_not_published_h2():
    facts = PolicyFacts(
        insurer=FactField(value="Reliance General", page=1),
        previousInsurer=FactField(value=None, page=1),
        businessType=FactField(value="unknown", page=1),
        policyType=FactField(value="comprehensive", page=1),
        make=FactField(value="RENAULT", page=1),
        model=FactField(value="KWID", page=1),
        fuel=FactField(value="petrol", page=1),
        rto=FactField(value="UP-16", page=1),
        printedLocation=FactField(value="NOIDA", page=1),
        premiums=PremiumBreakup(netOd=4714.0, page=1)
    )
    grid = registry.get_grid("reliance")
    res = resolve_policy(facts, grid)
    assert res.rates["tp"].state == ComponentState.UNSUPPORTED
    assert "H2" in res.rates["tp"].citations[0]["coordinate"]

def test_rule_tata_gwp_refusal():
    facts = PolicyFacts(
        insurer=FactField(value="TATA AIG", page=1),
        previousInsurer=FactField(value="TATA AIG", page=1),
        businessType=FactField(value="renewal", page=1),
        policyType=FactField(value="stand_alone_tp", page=1),
        make=FactField(value="MARUTI", page=1),
        model=FactField(value="ZEN ESTILO", page=1),
        fuel=FactField(value="cng", page=1),
        rto=FactField(value="DL-9C", page=1),
        printedLocation=FactField(value="DELHI", page=1),
        engineCc=FactField(value=998, page=1),
        vehicleAgeYears=FactField(value=15, page=1),
        premiums=PremiumBreakup(netTp=2154.0, page=1)
    )
    grid = registry.get_grid("tata_aig")
    res = resolve_policy(facts, grid)
    assert res.status == RunStatus.UNSUPPORTED
    assert res.rates["tp"].state == ComponentState.UNSUPPORTED
    assert res.rates["tp"].ratePercent is None
    assert any("Pvtcar!F3" in str(t.gridCitation) for t in res.trace)

def test_rule_missing_geography_mapping():
    # Unknown unmappable location
    facts = PolicyFacts(
        insurer=FactField(value="Go Digit", page=1),
        previousInsurer=FactField(value="Go Digit", page=1),
        businessType=FactField(value="renewal", page=1),
        policyType=FactField(value="stand_alone_tp", page=1),
        make=FactField(value="HYUNDAI", page=1),
        model=FactField(value="SANTRO", page=1),
        fuel=FactField(value="petrol", page=1),
        rto=FactField(value="XX-99", page=1),
        printedLocation=FactField(value="Atlantis Nonexistent City", page=1),
        premiums=PremiumBreakup(netTp=1000.0, page=1)
    )
    grid = registry.get_grid("godigit")
    res = resolve_policy(facts, grid)
    assert res.status in [RunStatus.AMBIGUOUS, RunStatus.UNSUPPORTED]
