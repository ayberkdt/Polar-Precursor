from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def gfz_daily_path() -> Path:
    """Real GFZ rows for 2003-07-01 .. 2003-12-31 with the original 40-line header."""
    return FIXTURES / "gfz_kp_ap_f107_2003H2_excerpt.txt"


@pytest.fixture(scope="session")
def gfz_hpo_path() -> Path:
    """Real Hp30/ap30 rows for 2003-10-27 .. 2003-11-01 with the original header."""
    return FIXTURES / "gfz_hp30_20031027_1101_excerpt.txt"


@pytest.fixture(scope="session")
def omni_path() -> Path:
    """Real OMNI HRO 1-minute records for 2003 days 301-303 (28-30 October)."""
    return FIXTURES / "omni_min_2003_doy301_303_excerpt.asc"
