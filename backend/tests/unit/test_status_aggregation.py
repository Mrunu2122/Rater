import pytest
from backend.app.resolver.states import ComponentState, RunStatus, RateComponent
from backend.app.resolver.status_aggregation import aggregate_run_status

def test_aggregation_od_resolved_tp_not_published():
    rates = {
        "od": RateComponent(applicable=True, ratePercent=17.5, state=ComponentState.RESOLVED, reason="OD resolved"),
        "tp": RateComponent(applicable=True, ratePercent=None, state=ComponentState.NOT_PUBLISHED, reason="TP not published in grid per H2")
    }
    assert aggregate_run_status(rates) == RunStatus.RESOLVED

def test_aggregation_od_unsupported_tp_not_published():
    rates = {
        "od": RateComponent(applicable=True, ratePercent=None, state=ComponentState.UNSUPPORTED, reason="Unsupported OD"),
        "tp": RateComponent(applicable=True, ratePercent=None, state=ComponentState.NOT_PUBLISHED, reason="TP not published")
    }
    assert aggregate_run_status(rates) == RunStatus.UNSUPPORTED

def test_aggregation_od_not_applicable_tp_resolved():
    rates = {
        "od": RateComponent(applicable=False, ratePercent=None, state=ComponentState.NOT_APPLICABLE, reason="SATP policy"),
        "tp": RateComponent(applicable=True, ratePercent=29.5, state=ComponentState.RESOLVED, reason="TP resolved")
    }
    assert aggregate_run_status(rates) == RunStatus.RESOLVED

def test_aggregation_od_ambiguous_tp_not_published():
    rates = {
        "od": RateComponent(applicable=True, ratePercent=None, state=ComponentState.AMBIGUOUS, reason="Missing fuel input"),
        "tp": RateComponent(applicable=True, ratePercent=None, state=ComponentState.NOT_PUBLISHED, reason="TP not published")
    }
    assert aggregate_run_status(rates) == RunStatus.AMBIGUOUS

def test_aggregation_both_unsupported():
    rates = {
        "od": RateComponent(applicable=True, ratePercent=None, state=ComponentState.UNSUPPORTED, reason="OD unsupported"),
        "tp": RateComponent(applicable=True, ratePercent=None, state=ComponentState.UNSUPPORTED, reason="TP unsupported")
    }
    assert aggregate_run_status(rates) == RunStatus.UNSUPPORTED
