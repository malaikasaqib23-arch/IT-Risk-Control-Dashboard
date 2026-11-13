# Remaining dashboard acceptance — 13 November 2026

[Fact] This update uses the existing `data/` folder. The user subsequently authorized filling the 15 missing synthetic control links; all other incident fields and existing links are preserved.

| Audit item | Result |
|---|---|
| Failed quality check must show red | [Fact] All failed checks now show red; critical invalid data stops calculations, review-level missing values remain inspectable. |
| Risk-band selection consistent across pages | [Fact] Band filters now select controls and their linked tests/incidents as well as risk records, using the active scoring basis. Unlinked incidents are excluded when control selection is restricted. |
| Heatmap selection and dropdowns | [Design choice] Native Plotly point selection is added to the rounded tiles; existing dropdowns are retained and synchronized as the accessible fallback. Browser selection verified for three cells in addition to parser tests; all25 dropdown/table/export combinations independently audited. |
| Caught/missed public scenarios | [Fact] Baseline alert page includes a public scenario table with six expected alerts and one expected non-alert. It is evaluated only with unrestricted baseline filters; other views request a reset. This does not read a private answer key. |
| Unlinked existing incidents | [Fact] All 110 incidents now have valid control links. The 15 type-based synthetic assignments are documented in SYNTHETIC_INCIDENT_LINK_REVIEW.csv; affected stored risks and the fixed-seed generator are synchronized. |
| Historical dates versus current snapshots | [Design choice] Event dates filter historical events; snapshot health/risk remain at the fixed report date. This preserves the agreed meaning; supervisor acceptance of the scope still needs recording. |
| Manual calculations and human testing | [Assumption] Student manual sign-off, colleague usability results, independent README onboarding and supervisor approvals remain pending. USABILITY_CHECKLIST.md contains questions and blank recording fields, not invented results. |
| Framework source corroboration | [Assumption] Existing SOURCE_LOG.csv verification gaps remain open; calculation tests do not establish ISO/CSF mapping correctness or regulator applicability. |

[Design choice] Do not claim full guide acceptance while human/source verification remains unresolved. Software completion, data acceptance and supervisor approval are separate review decisions.


[Design choice] Synthetic link repair: fill only previously blank control_id values by incident type (Malware -> CTRL-011; Unauthorized Access -> CTRL-002; Configuration Issue -> CTRL-013; Suspicious Activity -> CTRL-016; Service Disruption -> CTRL-006; Data Exposure -> CTRL-018). These are fictional assignments, not evidence of incident causes. Existing links are unchanged.
[Fact] The link-complete baseline has 17 open High/Critical risks (15 Critical). Health and event totals are unchanged; stored scores match recomputed scores. Earlier baseline results above describe the pre-repair dataset.
