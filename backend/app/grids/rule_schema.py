from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

class GridCitation(BaseModel):
    sourceType: str = "grid" # "grid" or "policy"
    file: str
    sheet: Optional[str] = None
    page: Optional[int] = None
    coordinate: Optional[str] = None # e.g. "B1609:C1609", "Table 2 Row 5 Col 3"
    description: str

class RateRule(BaseModel):
    ruleId: str
    insurer: str
    productSegment: str # "pvt_car"
    policyType: str # "comprehensive", "stand_alone_tp", "stand_alone_od"
    fuelTypes: List[str] # ["petrol"], ["diesel"], ["cng"], ["all"], etc.
    geographyType: str # "zone", "cluster", "city", "all"
    geographyKey: str # "Zone-1", "Zone-2", "UP_Bad", "Delhi", etc.
    ccMin: Optional[float] = None
    ccMax: Optional[float] = None
    vehicleAgeMin: Optional[float] = None
    vehicleAgeMax: Optional[float] = None
    premiumSlabMin: Optional[float] = None
    premiumSlabMax: Optional[float] = None
    slabOperator: Optional[str] = None # "<", ">-", "exact"
    businessType: Optional[str] = None # "new", "renewal", "rollover", "all"
    ncbRequired: Optional[bool] = None
    odRatePercent: Optional[float] = None
    tpRatePercent: Optional[float] = None
    citation: GridCitation
    notes: Optional[str] = None

class NormalizedGrid(BaseModel):
    insurerId: str
    insurerName: str
    fileName: str
    filePath: str
    checksumSha256: str
    effectiveFrom: Optional[str] = None
    effectiveTo: Optional[str] = None
    effectiveDateCaveat: Optional[str] = None
    rules: List[RateRule] = Field(default_factory=list)
    geographyMapping: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    footnotes: List[Dict[str, Any]] = Field(default_factory=list)
