"""Reproducibility without touching the reviewed baseline."""
import hashlib
from pathlib import Path
import subprocess
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_one_command_generator_is_repeatable_and_preserves_baseline(tmp_path):
    source = sorted((ROOT / "data").glob("*.csv"))
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source}
    first, second = tmp_path / "first", tmp_path / "second"
    for output in [first, second]:
        subprocess.run([sys.executable, str(ROOT / "generate_data.py"), "--output-dir", str(output)],
                       cwd=tmp_path, check=True, capture_output=True, text=True)
    expected_rows = {"SYNTHETIC_controls_DRAFT.csv": 19, "SYNTHETIC_control_tests.csv": 300,
                     "SYNTHETIC_incidents.csv": 110, "SYNTHETIC_risk_register.csv": 19}
    assert {p.name for p in first.glob("*.csv")} == set(expected_rows)
    for filename, count in expected_rows.items():
        a, b = pd.read_csv(first / filename), pd.read_csv(second / filename)
        assert len(a) == count
        pd.testing.assert_frame_equal(a, b)
        pd.testing.assert_frame_equal(a, pd.read_csv(ROOT / "data" / filename))
        if filename == "SYNTHETIC_incidents.csv":
            assert a.control_id.notna().all()
    assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source}
