"""Fixtures de teste: banco SQLite em memória, isolado por teste."""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import db  # noqa: E402


@pytest.fixture()
def engine():
    eng = db.init_db(db.get_engine("sqlite://"))  # SQLite em memória (StaticPool)
    yield eng
    eng.dispose()
