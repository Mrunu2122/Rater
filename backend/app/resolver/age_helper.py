import re
from datetime import datetime
from typing import Optional, Tuple

def extract_year_from_date_str(date_str: Optional[str]) -> Optional[int]:
    if not date_str or not isinstance(date_str, str):
        return None
    # Check 4-digit year like 2025, 2026, 2023
    m = re.search(r'\b(19\d\d|20\d\d)\b', date_str)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return None

def calculate_vehicle_age(
    policy_start_date: Optional[str],
    registration_year: Optional[int],
    manufacture_year: Optional[int] = None
) -> Tuple[Optional[int], str]:
    """
    Computes vehicleAgeYears from policy start date and registration year (or manufacture year).
    Returns (age_years, explanation_string).
    """
    pol_year = extract_year_from_date_str(policy_start_date)
    ref_year = pol_year or 2026
    
    base_year = registration_year or manufacture_year
    if base_year is None:
        return None, "Registration year and manufacture year not available"
        
    try:
        base_yr_int = int(base_year)
        age = max(0, ref_year - base_yr_int)
        source = "registration year" if registration_year else "manufacture year"
        return age, f"{ref_year} (policy start year) - {base_yr_int} ({source}) = {age} yrs"
    except Exception as e:
        return None, f"Could not calculate vehicle age: {e}"
