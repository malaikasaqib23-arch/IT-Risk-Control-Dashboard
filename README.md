# Week 4 — IT Risk & Control Monitoring Dashboard (Prototype v1)

**All files and records are SYNTHETIC.** Reporting date is fixed at **2026-10-31** for reproducible comparison with the Week 3 validation report. No client data, live connections, or credentials are required.

## Prerequisites
- Python 3.11+ (Windows, macOS or Linux)
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
- Control health: Pass 100, Partial 50, Fail 0. Latest test as of 2026-10-31. Untested controls excluded from mean and reported in coverage.
- Overdue test: > 1.5 × interval, with 30/90/180/365 day prototype intervals. Never tested flagged separately.
- Risk band thresholds: 1–4 Low; 5–9 Medium; 10–16 High; 17–25 Critical. Likelihood 1–5, impact 1–5; these are design choices, not official ISO/NIST score scales.
- Heatmap: each cell shows the count of open risk records with a given likelihood and impact. Select a point/cell to show underlying records.
- Date selection controls historical incidents and displayed historical test pass rate/exception events. Snapshot metrics (current control health, due dates and risk status) remain as of the fixed reference date, to avoid mixing event filters with point-in-time state. CSF and owner filters apply to controls and linked records; risk band filters apply to risk records.
- Incident spike rule: >= 10 incidents in a month and >= 2 × median of the other months in the selected incident series. The threshold is illustrative.
- Rule-based alerts are *prototype early implementation*: tested anomalies remain the reference cases. Week 5 adds fuller acceptance testing, usability feedback and systematic alert refinement.
- The project guide requires **three hand-verified dashboard examples** before approval. Compare the overview KPI output with the Week 3 report and check three selected controls/risks manually against CSV records. Do not mark supervisor sign-off complete automatically.

## Expected baseline values (no filters, as of 2026-10-31)
From Week 3 script: 19 controls, overall control health 73.68%; 1 overdue control; 16 open High/Critical risks; 110 incidents over 12 months. The 90-day incident total and on-time test share are calculated live on the dashboard and must be verified separately.

## Scope and safety
Data are fictional and not an audit opinion. NIST CSF mappings, scoring thresholds and some status semantics still require supervisor approval. Live system integrations, real client data, authentication, and predictive claims are out of scope.
