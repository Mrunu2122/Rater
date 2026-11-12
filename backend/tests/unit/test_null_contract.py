import pytest
from backend.app.resolver.states import FactField, PolicyFacts, PremiumBreakup

def test_null_value_field_contract():
    """Missing facts must be JSON None with a separate uncertainty field, never text sentences."""
    fuel_field = FactField(value=None, page=1, uncertainty="Fuel type not printed on policy", lowConfidence=True)
    assert fuel_field.value is None
    assert fuel_field.uncertainty == "Fuel type not printed on policy"
    assert fuel_field.lowConfidence is True

def test_policy_facts_null_serialization():
    facts = PolicyFacts(
        insurer=FactField(value="Reliance General Insurance Company Limited", page=2),
        previousInsurer=FactField(value=None, page=13, uncertainty="Not printed", lowConfidence=True),
        businessType=FactField(value="unknown", page=2),
        policyType=FactField(value="comprehensive", page=2),
        make=FactField(value="RENAULT", page=2),
        model=FactField(value="KWID", page=2),
        fuel=FactField(value=None, page=2, uncertainty="Fuel type not printed on policy", lowConfidence=True),
        rto=FactField(value="UP-16", page=2),
        premiums=PremiumBreakup(total=8535.0, page=2)
    )
    d = facts.model_dump()
    assert d["fuel"]["value"] is None
    assert d["fuel"]["uncertainty"] == "Fuel type not printed on policy"
    assert d["previousInsurer"]["value"] is None
    assert d["businessType"]["value"] == "unknown"
