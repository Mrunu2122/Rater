from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ComponentState(str, Enum):
    RESOLVED = "resolved"
    UNSUPPORTED = "unsupported"
    AMBIGUOUS = "ambiguous"
    NOT_APPLICABLE = "not_applicable"

class RunStatus(str, Enum):
    RESOLVED = "resolved"
    UNSUPPORTED = "unsupported"
    AMBIGUOUS = "ambiguous"

class FactField(BaseModel):
    value: Any
    page: Optional[int] = None
    confidence: float = 1.0 # 0.0 to 1.0
    uncertainty: Optional[str] = None
    lowConfidence: bool = False

class PremiumBreakup(BaseModel):
    basicOd: Optional[float] = None
    ncbDiscount: Optional[float] = None
    netOd: Optional[float] = None
    basicTp: Optional[float] = None
    netTp: Optional[float] = None
    taxes: Optional[float] = None
    total: Optional[float] = None
    page: Optional[int] = None
    confidence: float = 1.0
    ncbPercent: Optional[float] = None
    ncbUnclearNote: Optional[str] = None

class PolicyFacts(BaseModel):
    insurer: FactField
    previousInsurer: FactField
    businessType: FactField # "new", "renewal", "rollover", "unknown"
    policyType: FactField # "comprehensive", "stand_alone_tp", "stand_alone_od"
    make: FactField
    model: FactField
    fuel: FactField
    rto: FactField
    printedLocation: Optional[FactField] = None # e.g. state/city printed on policy
    engineCc: Optional[FactField] = None
    registrationYear: Optional[FactField] = None
    manufactureYear: Optional[FactField] = None
    vehicleAgeYears: Optional[FactField] = None # Derived
    policyStartDate: Optional[FactField] = None
    premiums: PremiumBreakup

class RateComponent(BaseModel):
    applicable: bool
    ratePercent: Optional[float] = None
    state: ComponentState
    reason: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)

class TraceStep(BaseModel):
    step: int
    decision: str
    policyCitation: Optional[str] = None
    gridCitation: Optional[str] = None
    explanation: str

class ResolverResult(BaseModel):
    status: RunStatus
    rates: Dict[str, RateComponent] # "od", "tp"
    confidence: Dict[str, Any] # { "level": 0-100, "reason": str }
    trace: List[TraceStep]
    appliedGridChecksum: str
    resolverVersion: str = "1.0.0"
