# SYNTHETIC validation evidence — student review required

[Fact] Source counts independently reconciled with the standard-library CSV reader, separately from pandas/dashboard formulas. [Assumption] Automated reconciliation does not replace the student's required manual review; check source rows and initial/date these examples.

## Three dashboard reconciliations

[Design choice] Snapshot date=2026-10-31 in all views. Health=(12×100+4×50+3×0)/19=1400/19=73.68%. On time=(19−1)/19×100=94.74%. Open High/Critical=5+11=16. Event windows change historical indicators only.

| Event range | 90-day incidents | Historical pass rate | Overdue controls | Open findings | Overdue remediation |
|---|---|---|---|---|---|
| [Fact] 2025-11-01–2026-10-31 | 41 within Aug3–Oct31 | 224/300×100=74.67% | 1 | 60 | 52/60×100=86.67% |
| [Fact] September 2026 | 30 | 20/29×100=68.97% | 1 | 7 | 7/7×100=100% |
| [Fact] October 2026 | 5 | 14/24×100=58.33% | 1 | 8 | 0/8×100=0% |

[Fact] Old 38 last-90-day incidents counted linked rows only; unrestricted total is 41. Source CSVs were not relinked or regenerated.

## Worked numerical examples

- [Design choice] Risk: 0 failures+0 incidents -> likelihood1 × impact3=3 Low; 1 failure+1 incident -> likelihood3 × impact4=12 High; 3 failures+0 incidents -> likelihood4 × impact5=20 Critical. Six events cap at likelihood5.
- [Design choice] Monthly overdue: 44 days=False, 45=False, 46=True, because 1.5×30=45 and comparison is strict. Never tested=True and zero health.
- [Design choice] Spike: preceding3,6,9 -> mean6 and threshold12; current12 triggers. Preceding0,0,0 -> threshold10; current10 triggers. Preceding10,10,10 -> threshold20; current19 does not. Current9 never meets the floor.
- [Fact] Baseline September: June9+July10+August7=26; mean26/3=8.6667; threshold17.3333; current30 triggers.
- [Design choice] KPI fixture A: health(100+50+0)/3=50%; on time1/3=33.33%; open High/Critical2; 90-day incidents2; Pass1/3=33.33%; overdue2; findings2; late1/2=50%; coverage2/3=66.67%.
- [Design choice] KPI fixture B: health(100+100)/2=100%; on time2/2=100%; open High/Critical0; incidents0; Pass2/2=100%; overdue0; findings0; late0/0=N/A; coverage2/2=100%.
- [Design choice] KPI fixture C: health(0+0)/2=0%; on time0/2=0%; open High/Critical1; incidents1; Pass0/1=0%; overdue2; findings1; late1/1=100%; coverage1/2=50% (one tested failed control and one never-tested control).

## Public scenario acceptance

| Scenario | Expected rule/result | Evidence |
|---|---|---|
| [Fact] CTRL-009 | CONSECUTIVE_FAILURES; caught | TEST-0282 Oct7 Fail; TEST-0293 Oct14 Fail |
| [Fact] CTRL-016 | CONSECUTIVE_FAILURES; caught | TEST-0296 Oct18 Fail; TEST-0297 Oct22 Fail |
| [Fact] CTRL-014 | TEST_OVERDUE; caught | Last test Jun4; 149 days >45 |
| [Fact] September2026 | INCIDENT_SPIKE; caught | 30 >=17.3333 and >=10 |
| [Fact] CTRL-013 | OPEN_EXCEPTION; caught | Partial/open finding |
| [Fact] INC-0001 | CRITICAL_OPEN_INCIDENT; caught | Critical/Open |
| [Design choice] Temporary CTRL-009 blank risk owner | HIGH_CRITICAL_MISSING_OWNER; caught | Risk owner blank even though control department exists; isolated fixture only |
| [Fact] CTRL-014 pair | No consecutive alert | TEST-0183 Fail then TEST-0191 Pass |

[Assumption] Expected cases are asserted in integration tests; final pytest output is the execution record. The private answer key was not accessed, and a real-world false-positive rate cannot be inferred.

[Assumption] Remaining acceptance: student signs manual checks; supervisor approves rules/mappings; 2–3 colleagues complete usability testing; student completes source log and authored deliverables.


## Later browser interaction verification

- [Fact] Clicked likelihood3/impact4: one matching record, RISK-013; score3*4=12 High.
- [Fact] Clicked likelihood1/impact5: two matching records, RISK-002 and RISK-005; score1*5=5 Medium.
- [Fact] Clicked likelihood5/impact5: five matching records, RISK-009/012/014/017/018; score5*5=25 Critical.
- [Fact] Each browser click updated both dropdowns and the underlying table. Existing event-date and scoring-basis behavior was preserved.
