import pytest
from backend.app.resolver.states import FactField, PolicyFacts, PremiumBreakup

def test_hdfc_missing_fuel_strict_null():
    """Verify that unprinted fuel is stored as None with uncertainty, never text string."""
    facts = PolicyFacts(
        insurer=FactField(value="HDFC ERGO General Insurance Company Limited", page=1),
        previousInsurer=FactField(value="TATA AIG GENERAL INSURANCE CO.LTD.", page=1),
        businessType=FactField(value="rollover", page=1),
        policyType=FactField(value="comprehensive", page=1),
        make=FactField(value="MAHINDRA", page=1),
        model=FactField(value="BOLERO NEO-N10 (R)", page=1),
        fuel=FactField(value=None, page=1, uncertainty="Fuel type not printed on policy schedule", lowConfidence=True),
        rto=FactField(value="HR-26", page=1),
        printedLocation=FactField(value="GURGAON", page=1),
        premiums=PremiumBreakup(netOd=8053.0, page=1)
    )
    assert facts.fuel.value is None
    assert facts.fuel.uncertainty == "Fuel type not printed on policy schedule"
    assert facts.fuel.lowConfidence is True
