# Guide review — 13 November 2026

[Fact] All 15 scanned pages of `sources/internship project guide.pdf` were reviewed as images; the source was not changed. This is a technical review, not the student's methodology or user guide.

| Pages | Requirement | Implementation / remaining evidence |
|---|---|---|
| 1, 3, 11 | Synthetic/public only; pinned packages | [Fact] Original synthetic CSVs preserved; tested dependencies pinned. No integrations, login, secrets, or prediction claims added. |
| 1, 9 | Dashboard and handover pack | [Fact] Code, run instructions, generator, technical dictionary and relationship diagram supplied. [Assumption] Student handover and supervisor acceptance remain pending. |
| 2, 4, 12, 15 | Verify NIST, ISO, SBP and risk references | [Assumption] Framework claims and proposed mappings are not certified by code tests; source-log gaps remain explicit. |
| 3, 11, 14 | Source log, version/date, conflicting sources, updates | [Fact] `SOURCE_LOG.csv` records verification gaps. [Assumption] Student must complete corroboration and weekly updates. |
| 4 | Problem statement, glossary, framework explanation, scope approval | [Assumption] Student-owned materials and supervisor sign-off not fabricated or marked complete. |
| 5, 13 | 15–20 controls, department owners, ISO/CSF mapping reasons | [Fact] Existing 19 controls and written mapping/impact reasons preserved. [Assumption] Mapping and numbering correctness still requires source review. |
| 5, 6 | Four tables, keys, relationships, dictionary | [Fact] `DATA_MODEL.md` and `SYNTHETIC_DATA_DICTIONARY.csv` describe actual data; live checks validate keys and links. [Fact] Existing 15 unlinked incidents remain visible as a warning. |
| 5, 10 | Six to eight KPIs with formula/data/action | [Fact] Eight indicators and formula/data/action table on Overview; testing coverage shown separately. |
| 5 | Wireframes and 8–10 user stories | [Assumption] Student design evidence remains for student review. |
| 6 | Fixed seed and one-command regeneration | [Fact] Generator path corrected; separate `--output-dir` supports isolated reproducibility checks. Baseline is not regenerated. |
| 6 | Known anomalies, private answer key, realistic trends | [Fact] Public seeded cases retained; isolated fixtures test missing-owner behavior. [Assumption] Private 5–8 anomaly key not accessed; student must perform private-key acceptance. |
| 7, 9–10 | Four headline KPIs | [Fact] Health, on-time controls, open High/Critical risks and 90-day incidents implemented; source counts reconciled for full history, September and October. |
| 7, 9 | CSF/ISO bars, 5×5 count heatmap, linked control table | [Fact] Existing charts and reliable likelihood/impact dropdown drill-down preserved; color scale explicitly labels counts. |
| 7, 10 | Incident trend by month and severity | [Fact] Preserved; unfiltered totals now include unlinked incidents and reconcile with raw data. |
| 7–8, 10 | Modular calculations, unit tests, named alerts | [Fact] Shared KPI/risk/quality modules; overdue, consecutive failure, three-month spike, and missing-owner rules are active alongside supplemental alerts. |
| 7, 10 | Function/owner/date/band filters and CSV exports | [Fact] Preserved; event filters affect history, band affects risk records, and snapshots remain fixed at report date. |
| 8 | Three-month mean spike and justified threshold | [Design choice] Complete month >=10 incidents and >=2× preceding three complete months' mean; combines relative rise and a volume floor. Supervisor approval pending. |
| 8 | Caught/missed and false-positive testing | [Fact] Public scenarios asserted through the rendered table; positive/negative isolated fixtures test boundaries. [Assumption] These do not establish real-world false-positive rates. |
| 8 | Optional Isolation Forest | [Design choice] Omitted as a Could item; required rules and testing take priority. |
| 8–9 | Usability test with 2–3 colleagues, feature freeze | [Assumption] Human testing, feedback and supervisor review remain pending; no fabricated acceptance. |
| 8–9, 14–15 | Methodology, guide, slides, reflection, live demo | [Assumption] Student-owned deliverables, 15-minute presentation and 10-minute Q&A remain student work. |
| 10 | Data-quality banner becomes red on failure | [Fact] Live checks show details; critical failures stop calculations with a red banner. Temporary corrupted-fixture integration test covers this. |
| 10 | Scoring with worked examples | [Design choice] Never-tested health=0 and overdue=True; event likelihood uses (report−365 days, report]. Stored and recomputed ratings are selectable without writing CSVs. |
| 11 | Rubric: technical30/framework20/accuracy20/communication20/ownership10 | [Design choice] Modular logic, tests, traceable evidence and honest verification gaps prioritized over optional features. |

## Recorded conflicts

- [Fact] Previous spike used the median of other months; guide p.8 suggests a three-month average. [Design choice] Production rule and verifier now share the preceding-three-month mean.
- [Fact] Previous never-tested handling excluded health and returned not-overdue; guide p.10 calls no recent test overdue. [Design choice] Zero health plus separate coverage and never-tested flags adopted.
- [Fact] Previous unfiltered incident views dropped 15 unlinked rows. [Design choice] Include them when controls are unrestricted; do not invent control links. Subsequently resolved with user-authorized type-based synthetic assignments; see the review CSV.
- [Fact] Guide p.10 calls scoring a design choice; p.12 also says scales should be labelled assumptions. [Design choice] Chosen scales consistently labelled design choices pending approval.
- [Fact] Old README described heatmap clicks. [Design choice] Updated to the working dropdowns.

[Design choice] Dashboard implementation is separate from internship acceptance: source corroboration, private-key review, usability evidence, supervisor approvals and student writing remain open.


[Design choice] Synthetic link repair: fill only previously blank control_id values by incident type (Malware -> CTRL-011; Unauthorized Access -> CTRL-002; Configuration Issue -> CTRL-013; Suspicious Activity -> CTRL-016; Service Disruption -> CTRL-006; Data Exposure -> CTRL-018). These are fictional assignments, not evidence of incident causes. Existing links are unchanged.
[Fact] The link-complete baseline has 17 open High/Critical risks (15 Critical). Health and event totals are unchanged; stored scores match recomputed scores. Earlier baseline results above describe the pre-repair dataset.
