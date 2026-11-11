import pytest
from backend.app.grids.registry import registry

def test_godigit_parser_coordinates():
    grid = registry.get_grid("godigit")
    assert grid is not None
    assert len(grid.rules) > 100
    # Verify row citations have exact cell coordinates
    assert all(r.citation.coordinate is not None for r in grid.rules)
    assert any("B293:E293" in r.citation.coordinate for r in grid.rules)

def test_reliance_parser_coordinates():
    grid = registry.get_grid("reliance")
    assert grid is not None
    assert len(grid.rules) == 30
    assert any("A11:C11" in r.citation.coordinate for r in grid.rules)

def test_hdfc_parser_coordinates():
    grid = registry.get_grid("hdfc_ergo")
    assert grid is not None
    assert len(grid.rules) == 30
    assert any("Table 2 Row 5" in r.citation.coordinate for r in grid.rules)

def test_tata_parser_coordinates():
    grid = registry.get_grid("tata_aig")
    assert grid is not None
    assert len(grid.rules) > 1000
    assert any("V511" in r.citation.coordinate for r in grid.rules)
