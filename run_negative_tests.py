
"""
Week 3 - Negative Data Validation Tests

SYNTHETIC DATA ONLY

Tests three intentionally corrupted datasets:
1. Invalid foreign key
2. Incorrect risk score
3. Invalid incident status

The original CSV files are never modified.

Run:
    python run_negative_tests.py
"""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import pandas as pd


# ============================================================
# 1. PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

VALIDATOR = ROOT / "test_data_quality.py"

CSV_FILES = [
    "SYNTHETIC_controls_DRAFT.csv",
    "SYNTHETIC_control_tests.csv",
    "SYNTHETIC_incidents.csv",
    "SYNTHETIC_risk_register.csv",
]


# ============================================================
# 2. VERIFY REQUIRED FILES
# ============================================================

missing = []

if not VALIDATOR.is_file():
    missing.append("test_data_quality.py")

for filename in CSV_FILES:
    if not (DATA / filename).is_file():
        missing.append(f"data/{filename}")

if missing:
    print("ERROR: Required files are missing:")

    for filename in missing:
        print(f"  - {filename}")

    sys.exit(1)


# ============================================================
# 3. DEFINE NEGATIVE TEST CASES
# ============================================================

CASES = [
    {
        "name": "Invalid foreign key",
        "file": "SYNTHETIC_control_tests.csv",
        "column": "control_id",
        "bad_value": "CTRL-DOES-NOT-EXIST",
        "expected_check": "tests valid control FK",
    },
    {
        "name": "Incorrect risk score",
        "file": "SYNTHETIC_risk_register.csv",
        "column": "risk_score",
        "bad_value": None,
        "expected_check": "risk scores match",
    },
    {
        "name": "Invalid incident status",
        "file": "SYNTHETIC_incidents.csv",
        "column": "status",
        "bad_value": "NotARealStatus",
        "expected_check": "incident status allowed",
    },
]


# ============================================================
# 4. RUN NEGATIVE TESTS
# ============================================================

results = []

print("SYNTHETIC NEGATIVE VALIDATION TESTS")
print("-" * 65)

with tempfile.TemporaryDirectory(
    prefix="week3_negative_tests_"
) as temporary_folder:

    temp_root = Path(temporary_folder)

    for index, case in enumerate(CASES, start=1):

        # Create an isolated project structure
        case_root = temp_root / f"case_{index}"
        case_data = case_root / "data"

        case_data.mkdir(parents=True)

        # Copy the validator into the temporary project
        shutil.copy2(
            VALIDATOR,
            case_root / "test_data_quality.py"
        )

        # Copy all synthetic CSV files
        for filename in CSV_FILES:
            shutil.copy2(
                DATA / filename,
                case_data / filename
            )

        # Select the temporary CSV to corrupt
        csv_path = case_data / case["file"]

        df = pd.read_csv(csv_path)

        # Introduce exactly one invalid condition
        if case["name"] == "Incorrect risk score":

            correct_score = (
                int(df.loc[0, "likelihood"])
                * int(df.loc[0, "impact"])
            )

            df.loc[0, "risk_score"] = correct_score + 1

        else:

            df.loc[0, case["column"]] = case["bad_value"]

        # Save only the temporary corrupted CSV
        df.to_csv(
            csv_path,
            index=False
        )

        # Execute the validator against temporary files
        completed = subprocess.run(
            [
                sys.executable,
                str(case_root / "test_data_quality.py")
            ],
            cwd=case_root,
            capture_output=True,
            text=True
        )

        combined_output = (
            completed.stdout
            + "\n"
            + completed.stderr
        )

        # Confirm the intended validation check failed
        expected_message = (
            "AssertionError: "
            + case["expected_check"]
        )

        detected = (
            completed.returncode != 0
            and expected_message in combined_output
        )

        results.append(detected)

        status = "PASS" if detected else "FAIL"

        print(
            f"{status} | {case['name']} | "
            f"expected rejection: {case['expected_check']}"
        )

        if not detected:
            print("Unexpected validator output:")
            print(combined_output[-2000:])


# ============================================================
# 5. FINAL RESULTS
# ============================================================

passed = sum(results)
total = len(results)

print()
print(f"Negative tests passed: {passed}/{total}")

print(
    "Original CSV files were not modified. "
    "Temporary test copies have been deleted."
)

if passed != total:
    sys.exit(1)
