# Dashboard — IT Risk & Control Monitoring Dashboard (Prototype v2)

**All files and records are SYNTHETIC.** Reporting date is fixed at **2026-10-31** for reproducible comparison with the Week 3 validation report. No client data, live connections, or credentials are required.

## Prerequisites
- Python 3.13 (tested) (Windows, macOS or Linux)
- VS Code/terminal

## Run on Windows
Open a PowerShell terminal in this folder and run:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

The terminal will display a local URL (typically http://localhost:8501). Open it in your browser. Stop with Ctrl+C.

## Structure
- `app.py`: Streamlit dashboard and visualisations (Overview, Control Health, Risk Heatmap & Alerts)
- `scoring.py`: reusable health, risk, frequency, likelihood and aggregation rules
- `tests/test_scoring.py`: hand-checkable unit tests
- `data/`: four Week 3 CSV datasets; never replace with real client data
- `requirements.txt`: dependencies

## Interpretation notes
- Overview four headline metrics align with the guide: latest-result control health; percent of selected controls tested on time (excludes overdue and never tested); open High/Critical risk records; incidents during the last 90 days of the reporting period.
- Control health: Pass 100, Partial 50, Fail 0. Latest test as of 2026-10-31. [Design choice] Untested controls contribute 0 and count as overdue; coverage is reported separately.
- Overdue test: > 1.5 × interval, with 30/90/180/365 day prototype intervals. Never tested is overdue and flagged separately.
- Risk band thresholds: 1–4 Low; 5–9 Medium; 10–16 High; 17–25 Critical. Likelihood 1–5, impact 1–5; these are design choices, not official ISO/NIST score scales.
- Heatmap: each cell shows the count of open risk records with a given likelihood and impact. Use the working Likelihood/Impact dropdowns to show underlying records.
- Date selection controls historical incidents and displayed historical test pass rate/exception events. Snapshot metrics (current control health, due dates and risk status) remain as of the fixed reference date, to avoid mixing event filters with point-in-time state. CSF and owner filters apply to controls and linked records; risk band filters select the same controls and linked records across all pages.
- [Design choice] Incident spike: complete month >=10 incidents and >=2 times the arithmetic mean of the preceding three complete calendar months. Three complete predecessor months are required. Event filters select alert months; full eligible history supplies the baseline. Threshold approval is pending.
- [Design choice] Required named alerts: overdue tests, consecutive failures, three-month incident spike, and open High/Critical risks missing risk owners. Existing latest failure, open finding and critical incident alerts remain. Human usability testing and supervisor acceptance are pending.
- The project guide requires **three hand-verified dashboard examples** before approval. Compare the overview KPI output with the Week 3 report and check three selected controls/risks manually against CSV records. Do not mark supervisor sign-off complete automatically.

## Expected baseline values (no filters, as of 2026-10-31)
[Fact] Current link-complete baseline: 19 controls, health 73.68%; 1 overdue control; 17 open High/Critical risks; 110 incidents over 12 months; 41 in the last 90 days; 94.74% tested on time. All 110 incidents have valid control links.

## Scope and safety
Data are fictional and not an audit opinion. NIST CSF mappings, scoring thresholds and some status semantics still require supervisor approval. Live system integrations, real client data, authentication, and predictive claims are out of scope.


## Prototype v2 calculations and verification

- [Design choice] Default risk basis recomputes likelihood=min(1+failed tests+linked incidents,5), with events in (report date - 365 days, report date]. Partial is not Fail (assumption requiring approval). Impact is fixed by the control register. Stored mode remains selectable; no CSV is rewritten.
- [Design choice] Unlinked incidents are included only when all controls are selected. All 110 baseline incidents now have control links; the quality banner still detects future missing links; invalid nonblank links stop calculations. Historical filters never change snapshot health/risk, and risk band selects controls and linked records across all pages.
- [Fact] Eight visible indicators have formulas, required data and suggested manager actions in an Overview expander. Supporting coverage and missing due dates are explicit. Percentages with zero denominators display N/A.
- [Fact] Every failed quality check shows red; critical invalid data stops calculations, while review-level failures remain inspectable. File changes invalidate the data cache on rerun.
- [Fact] Last-90-day unfiltered incidents=41; the former display of38 dropped unlinked incidents. Baseline health=1400/19=73.68%, on-time=18/19=94.74%, High/Critical=16.
- [Fact] `monitoring.py` holds reusable KPI/event-risk logic; `quality.py` holds live checks. `REQUIREMENTS_REVIEW.md` maps every guide section; `VALIDATION.md` supplies worked examples for student review. `DATA_MODEL.md` and `SYNTHETIC_DATA_DICTIONARY.csv` describe the actual tables. `SOURCE_LOG.csv` records verification still needed.
- [Assumption] Framework mappings/numbering, source corroboration, student manual sign-off, private anomaly acceptance, colleague usability feedback and supervisor approvals remain pending. Automated checks do not certify compliance.

[Design choice] Exact tested package versions are pinned in requirements.txt (Python3.13 tested). For safe regeneration into a separate folder:

```powershell
python generate_data.py --output-dir generated-demo
```

[Design choice] This produces all four SYNTHETIC CSVs using fixed seed202611 and the existing control-register template. Running without --output-dir intentionally overwrites generated tables in data/; preserve the reviewed baseline unless regeneration is intended. Keep .venv and private answer keys ignored.

## Dashboard appearance

[Design choice] The reference-inspired dark navy theme uses cyan, violet, pink, and amber accents. Configuration lives in .streamlit/config.toml; dashboard.css styles the panels and metric cards; visuals.py supplies consistent Plotly presentation.

[Fact] Overview includes stacked monthly incident bars, a latest-control-result doughnut, and a monthly total area chart. Control Health includes CSF bars, a radar of the same health averages, and horizontal ISO-theme bars. Risk Heatmap & Alerts adds an open-risk-band doughnut beside the count heatmap. These display the existing calculations; they add no predictive or maturity scoring.


## Completed dashboard acceptance fixes

- [Fact] Clicking a heatmap tile selects its likelihood/impact pair and synchronizes the existing dropdowns; the dropdowns remain available.
- [Fact] Risk-band selection now filters controls and their linked historical records across pages. Historical date filters preserve the fixed reporting-date snapshot meaning.
- [Fact] The quality panel lists and exports existing unlinked incidents. Public baseline scenario checks appear beneath the alert table. Missing synthetic links were assigned by incident type with an explicit review log.
- [Assumption] Dataset link completeness, private answer-key review, manual signatures, framework corroboration and colleague testing still require review. See REMAINING_ACCEPTANCE.md and USABILITY_CHECKLIST.md.


[Design choice] Synthetic link repair: fill only previously blank control_id values by incident type (Malware -> CTRL-011; Unauthorized Access -> CTRL-002; Configuration Issue -> CTRL-013; Suspicious Activity -> CTRL-016; Service Disruption -> CTRL-006; Data Exposure -> CTRL-018). These are fictional assignments, not evidence of incident causes. Existing links are unchanged.
[Fact] The link-complete baseline has 17 open High/Critical risks (15 Critical). Health and event totals are unchanged; stored scores match recomputed scores. Earlier baseline results above describe the pre-repair dataset.
