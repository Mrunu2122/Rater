from typing import Dict
from backend.app.resolver.states import ComponentState, RunStatus, RateComponent

def aggregate_run_status(rates: Dict[str, RateComponent]) -> RunStatus:
    """
    Computes overall run status as the worst state among REQUIRED components,
    ignoring not_applicable and not_published.
    
    Status severity ranking (worst to best):
    1. UNSUPPORTED
    2. AMBIGUOUS
    3. RESOLVED
    
    If all applicable components are not_published, or no active components remain,
    it maps cleanly according to component availability.
    """
    active_states = []
    for comp in rates.values():
        if not comp.applicable:
            continue
        if comp.state in (ComponentState.NOT_APPLICABLE, ComponentState.NOT_PUBLISHED):
            continue
        active_states.append(comp.state)
        
    if not active_states:
        # If all applicable components are not_published
        published_or_supported = [c for c in rates.values() if c.applicable and c.state != ComponentState.NOT_PUBLISHED]
        if not published_or_supported and any(c.applicable and c.state == ComponentState.NOT_PUBLISHED for c in rates.values()):
            # All applicable components are not published by grid
            return RunStatus.UNSUPPORTED
        return RunStatus.RESOLVED

    if any(s == ComponentState.UNSUPPORTED for s in active_states):
        return RunStatus.UNSUPPORTED
    if any(s == ComponentState.AMBIGUOUS for s in active_states):
        return RunStatus.AMBIGUOUS
    if all(s == ComponentState.RESOLVED for s in active_states):
        return RunStatus.RESOLVED
        
    return RunStatus.UNSUPPORTED
