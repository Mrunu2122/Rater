import pytest
from backend.app.grids.registry import registry
from backend.app.resolver.resolver import resolve_policy
from backend.app.resolver.states import PolicyFacts, FactField, PremiumBreakup, ComponentState, RunStatus

def test_tata_fact_mutation():
    grid = registry.get_grid("tata_aig")
    assert grid is not None
    
    # 1. Facts with CNG & Renewal
    facts1 = PolicyFacts(
        insurer=FactField(value="Tata AIG", page=4),
        previousInsurer=FactField(value="Tata AIG", page=11),
        businessType=FactField(value="renewal", page=11),
        policyType=FactField(value="stand_alone_tp", page=4),
        make=FactField(value="MARUTI", page=4),
        model=FactField(value="ZEN ESTILO", page=4),
        fuel=FactField(value="CNG", page=4),
        rto=FactField(value="DELHI", page=4),
        printedLocation=FactField(value="DELHI", page=4),
        premiums=PremiumBreakup(total=3416.0, page=4)
    )
    res1 = resolve_policy(facts1, grid)
    assert res1.status == RunStatus.UNSUPPORTED
    # Trace step 4 is the candidate rows inspection step
    candidate_step = [t for t in res1.trace if "candidate rows" in t.decision.lower()][0]
    assert "CNG" in candidate_step.decision
    assert "renewal" in candidate_step.decision.lower()
    
    # 2. Mutate facts: Diesel & Rollover
    facts2 = PolicyFacts(
        insurer=FactField(value="Tata AIG", page=4),
        previousInsurer=FactField(value="HDFC ERGO", page=11),
        businessType=FactField(value="rollover", page=11),
        policyType=FactField(value="stand_alone_tp", page=4),
        make=FactField(value="MARUTI", page=4),
        model=FactField(value="ZEN ESTILO", page=4),
        fuel=FactField(value="Diesel", page=4),
        rto=FactField(value="DELHI", page=4),
        printedLocation=FactField(value="DELHI", page=4),
        premiums=PremiumBreakup(total=3416.0, page=4)
    )
    res2 = resolve_policy(facts2, grid)
    assert res2.status == RunStatus.UNSUPPORTED
    candidate_step2 = [t for t in res2.trace if "candidate rows" in t.decision.lower()][0]
    assert "Diesel" in candidate_step2.decision
    assert "rollover" in candidate_step2.decision.lower()

def test_godigit_mutation():
    grid = registry.get_grid("godigit")
    assert grid is not None
    
    # 1. Standard UP-78 (>1000 cc Petrol)
    facts1 = PolicyFacts(
        insurer=FactField(value="Go Digit", page=1),
        previousInsurer=FactField(value="Go Digit", page=2),
        businessType=FactField(value="renewal", page=2),
        policyType=FactField(value="stand_alone_tp", page=1),
        make=FactField(value="HYUNDAI", page=1),
        model=FactField(value="SANTRO", page=1),
        fuel=FactField(value="Petrol", page=1),
        rto=FactField(value="UP-78", page=1),
        engineCc=FactField(value=1086, page=1),
        vehicleAgeYears=FactField(value=7, page=1),
        premiums=PremiumBreakup(total=4089.88, page=2)
    )
    res1 = resolve_policy(facts1, grid)
    assert res1.rates["tp"].ratePercent == 29.5
    
    # 2. Mutate to an RTO not in grid
    facts2 = PolicyFacts(
        insurer=FactField(value="Go Digit", page=1),
        previousInsurer=FactField(value="Go Digit", page=2),
        businessType=FactField(value="renewal", page=2),
        policyType=FactField(value="stand_alone_tp", page=1),
        make=FactField(value="HYUNDAI", page=1),
        model=FactField(value="SANTRO", page=1),
        fuel=FactField(value="Petrol", page=1),
        rto=FactField(value="XX-99", page=1), # Non-existent RTO
        engineCc=FactField(value=1086, page=1),
        vehicleAgeYears=FactField(value=7, page=1),
        premiums=PremiumBreakup(total=4089.88, page=2)
    )
    res2 = resolve_policy(facts2, grid)
    assert res2.rates["tp"].state == ComponentState.UNSUPPORTED
    assert "missing" in res2.trace[2].explanation or "not found" in res2.trace[2].decision.lower()
