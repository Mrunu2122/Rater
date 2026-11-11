import os
import glob
from typing import Dict, Optional
from backend.app.grids.rule_schema import NormalizedGrid
from backend.app.grids.xlsx_parser import parse_godigit_grid, parse_reliance_grid, parse_tata_aig_grid
from backend.app.grids.pdf_parser import parse_hdfc_ergo_grid

class GridRegistry:
    def __init__(self, raters_dir: Optional[str] = None):
        if not raters_dir:
            # Look in data/raters or raters
            cands = [
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "raters"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "raters")
            ]
            for c in cands:
                if os.path.exists(c):
                    raters_dir = os.path.abspath(c)
                    break
        self.raters_dir = raters_dir
        self.grids: Dict[str, NormalizedGrid] = {}
        self.load_all()
        
    def load_all(self):
        if not self.raters_dir or not os.path.exists(self.raters_dir):
            return
            
        # 1. Go Digit
        digit_files = glob.glob(os.path.join(self.raters_dir, "godigit", "**", "*.xlsx"), recursive=True)
        if digit_files:
            self.grids["godigit"] = parse_godigit_grid(digit_files[0])
            
        # 2. Reliance
        reliance_files = glob.glob(os.path.join(self.raters_dir, "reliance*", "**", "*.xlsx"), recursive=True)
        if reliance_files:
            self.grids["reliance"] = parse_reliance_grid(reliance_files[0])
            
        # 3. Tata AIG
        tata_files = glob.glob(os.path.join(self.raters_dir, "tata*", "**", "*.xlsx"), recursive=True)
        if tata_files:
            self.grids["tata_aig"] = parse_tata_aig_grid(tata_files[0])
            
        # 4. HDFC ERGO
        hdfc_files = glob.glob(os.path.join(self.raters_dir, "hdfc*", "**", "*.pdf"), recursive=True)
        if hdfc_files:
            self.grids["hdfc_ergo"] = parse_hdfc_ergo_grid(hdfc_files[0])
            
    def get_grid(self, insurer_id: str) -> Optional[NormalizedGrid]:
        return self.grids.get(insurer_id)
        
    def get_all(self) -> Dict[str, NormalizedGrid]:
        return self.grids

registry = GridRegistry()
