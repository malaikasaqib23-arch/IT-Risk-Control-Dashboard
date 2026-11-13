# SYNTHETIC execution record - 13 November 2026

- [Fact] Final execution folder: existing IT Risk And Control Monitoring Dashboard project.
- [Fact] python -m pytest -q: 65 passed in 54.24 seconds.
- [Fact] python test_data_quality.py: 21/21 legacy baseline checks passed.
- [Fact] python analyze_data.py: all eight baseline analysis calculations completed.
- [Fact] python verify_anomalies.py: 5/5 deterministic public scenarios passed using the production three-month spike rule.
- [Fact] python run_negative_tests.py: 3/3 intentionally corrupted temporary datasets rejected.
- [Fact] Generator integration test reproduced all four output tables twice in temporary folders and preserved baseline source hashes.
- [Fact] Live dashboard at localhost:8501 showed Prototype v2, eight Overview indicators, and consecutive-failure alerts with source test identifiers.
- [Fact] Overview: 73.68% health; 94.74% on time; 16 open High/Critical; 41 incidents in 90 days; 74.67% historical pass rate; 1 overdue control; 60 unresolved findings; 86.67% overdue remediation.
- [Fact] Live quality results: 38 of 39 checks pass; one warning identifies 15 existing unlinked incidents. This is separate from the 21 legacy baseline assertions. The red-banner test verifies that a critical failure stops calculation.
- [Fact] SHA256 integrity comparison: all four original synthetic source CSVs unchanged.
- [Fact] git diff --check passed; staged diff empty; no commit or push performed.
- [Assumption] Manual student signature, private answer-key review, colleague usability evidence, source corroboration and supervisor approvals remain pending. See REQUIREMENTS_REVIEW.md and VALIDATION.md.

## UI theme verification - 13 November 2026

- [Fact] Updated navy/cyan/violet/pink presentation and new charts: 74 tests passed in the original project folder (59.68 seconds).
- [Fact] Nine chart checks cover counts, empty selections, exact monthly totals, and fixed radar scale; existing dashboard/filter/scoring tests pass.
- [Design choice] Added latest-result doughnut, monthly incident area, CSF health radar, horizontal ISO bars, and risk-band doughnut. Required stacked severity bars and count heatmap remain.
- [Fact] Styling is isolated in .streamlit/config.toml, dashboard.css, and visuals.py. Scoring modules, source datasets and thresholds were not changed by this UI update.
- [Fact] No changes staged or committed.

## Remaining dashboard software fixes - 13 November 2026

- [Fact] Final project suite: 88 passed in 69.56 seconds. Added checks cover selection payloads, public scenario failures, red review-level quality status and cross-page risk-band filtering.
- [Fact] Browser cell clicks synchronized dropdowns and displayed records: likelihood3/impact4 -> RISK-013 (1 record); likelihood1/impact5 -> RISK-002 and RISK-005 (2 records); likelihood5/impact5 -> RISK-009/012/014/017/018 (5 records).
- [Fact] Independent raw-CSV audit passed all25 cells, their exported tables, CSF/ISO group means and monthly severity totals. Source CSV hashes remain unchanged.
- [Fact] Public seeded verification passed5/5 and negative data validation passed3/3.
- [Fact] Missing baseline control links remain15, as requested when retaining the existing dataset; these are listed and exportable in the red quality panel. This is a data acceptance issue, not a passing completeness claim.
- [Fact] The local server was restarted to load the updated helper module and the working dashboard was verified in the browser. No commit or push performed.


## Synthetic control-link repair - 13 November 2026

- [Design choice] User authorized filling 15 blank incident links using the documented type-based synthetic map; SYNTHETIC_INCIDENT_LINK_REVIEW.csv lists each assignment.
- [Fact] All 110 incidents now have valid control links. Existing links and every other incident field are preserved; controls and control_tests retain their original SHA256 hashes.
- [Fact] Stored scores updated only for CTRL-002, CTRL-006, CTRL-011 and CTRL-013. Hand-count checks: 0 failures + 3 incidents -> likelihood4 * impact5 =20 for CTRL-002 and CTRL-006; 0+8 -> capped likelihood5 * impact5 =25 for CTRL-011; 0+5 -> capped likelihood5 * impact4 =20 for CTRL-013.
- [Fact] 97 pytest checks passed in 22.20 seconds, including exact generator reproduction of all four revised baseline tables, link preservation, rejection of unknown missing-link types, and continued detection of future missing links.
- [Fact] Independent audit passed all25 heatmap cells, tables and CSV exports; chart totals and alert exports reconcile. Public anomalies5/5 and negative validation3/3 passed.
- [Fact] Live dashboard displays39/39 quality checks passed and17 open High/Critical risks. Health73.68%, on-time94.74% and last90-day incidents41 remain unchanged.
- [Fact] No staging or commit performed. Earlier results in this log describe earlier dataset versions.
