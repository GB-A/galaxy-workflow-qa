# Test Cases

Synthetic-data test suite for a locally hosted Galaxy instance. Nothing here is real protein or Portal Biotech data.

**How to read this:** every test case maps to a requirement (`REQ-xxx`) via a `@pytest.mark.req("REQ-xxx")` marker, so the traceability matrix can be generated from the code.
Priority: **P1** = must pass for the build to be trusted, **P2** = important, **P3** = nice to have.
"Expected" results marked *(explore first)* are behaviours to be observed on the real instance and then locked in, not assumed.

## Reference data

Fixture `data/reads.tabular` (read ID, length, quality, protein):

| read | length | quality | protein |
|---|---|---|---|
| r1 | 120 | 35 | P1 |
| r2 | 80 | 12 | P2 |
| r3 | 200 | 28 | P1 |
| r4 | 150 | 18 | P3 |
| r5 | 90 | 40 | P2 |

Hand-derived expectations (golden files in `data/golden/`):

- `quality_filtered` (`c3>=20`): r1, r3, r5
- `sorted_reads` (column 3, descending): r5, r1, r3
- `protein_counts` (column 4): P1 = 2, P2 = 1 (confirm column order in real output)

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | An uploaded tab-separated file is recognised as datatype `tabular` |
| REQ-002 | An uploaded dataset reaches the `ok` state |
| REQ-003 | The workflow can be imported and has the expected steps, tool IDs and typed input |
| REQ-004 | A workflow invocation can be launched via the API and completes with all jobs `ok` |
| REQ-005 | The workflow excludes reads with quality < 20 |
| REQ-006 | The workflow sorts retained reads by quality, descending |
| REQ-007 | The workflow reports read counts per protein |
| REQ-008 | Workflow outputs match the approved golden files |
| REQ-009 | A user can launch the workflow from the UI |
| REQ-010 | A user can follow run progress in the history and see completion |
| REQ-011 | UI and API report consistent results for the same run |
| REQ-012 | Protected API endpoints reject missing or invalid credentials |
| REQ-013 | Invalid or malformed input fails cleanly with a readable error |
| REQ-014 | Repeated or concurrent runs are independent |
| REQ-015 | An empty input dataset is handled without hanging or a silent success |
| REQ-016 | A user can author the workflow in the editor |
| REQ-017 | Key pages have no critical accessibility violations |
| REQ-018 | The workflow completes within the agreed time budget on the fixture |
| REQ-019 | A user cannot access another user's histories or datasets |
| REQ-020 | Test runs leave no residual data (isolation and cleanup) |

## 1. Harness and smoke

| ID | Title | Steps | Expected | Req | Pri |
|---|---|---|---|---|---|
| TC-SMK-001 | Galaxy reachable and versioned | GET `/api/version` | 200, version string present (recorded in report) | REQ-004 | P1 |
| TC-SMK-002 | API key authenticates | GET `/api/users/current` with key | 200, expected admin user | REQ-012 | P1 |
| TC-SMK-003 | Built-in tool run | Upload text, run `cat1`, download | Output equals input | REQ-004 | P1 |
| TC-SMK-004 | Required tools installed | GET `/api/tools`, look for `Filter1`, `sort1`, `Count1` | All present at pinned versions | REQ-003 | P1 |

## 2. API tests

| ID | Title | Steps | Expected | Req | Pri |
|---|---|---|---|---|---|
| TC-API-001 | Upload type detection | Upload `reads.tabular` via API | Dataset reaches `ok`, extension `tabular` | REQ-001, REQ-002 | P1 |
| TC-API-002 | Workflow import | Import `reads_qc.gxwf.yml` | Import succeeds, workflow id returned | REQ-003 | P1 |
| TC-API-003 | Workflow structure | Fetch imported workflow | Steps: input `reads` (tabular), `Filter1`, `sort1`, `Count1`; connections as designed; tool versions pinned | REQ-003 | P1 |
| TC-API-004 | Invoke workflow | POST invocation with fixture | Invocation created, state reaches `scheduled` | REQ-004 | P1 |
| TC-API-005 | All jobs complete | Poll jobs for the invocation (with timeout) | Every job `ok`, none `error` | REQ-004 | P1 |
| TC-API-006 | Filter output correct | Download `quality_filtered` | Matches golden: r1, r3, r5 | REQ-005, REQ-008 | P1 |
| TC-API-007 | Sort output correct | Download `sorted_reads` | Matches golden: r5, r1, r3 | REQ-006, REQ-008 | P1 |
| TC-API-008 | Count output correct | Download `protein_counts` | Matches golden: P1=2, P2=1 | REQ-007, REQ-008 | P1 |
| TC-API-009 | Boundary: quality exactly 20 | Fixture variant with a read at quality 20 | Read is retained (`>=`) | REQ-005 | P2 |
| TC-API-010 | Boundary: quality 19 | Fixture variant with a read at quality 19 | Read is excluded | REQ-005 | P2 |
| TC-API-011 | Ties in sort key | Two reads with equal quality | Order is deterministic across runs *(explore first)* | REQ-006 | P3 |
| TC-API-012 | Missing API key | Request protected endpoint with no key | 401/403, no data in body *(explore first)* | REQ-012 | P1 |
| TC-API-013 | Invalid API key | Request with a malformed/unknown key | 401/403, same contract as above *(explore first)* | REQ-012 | P1 |
| TC-API-014 | Malformed rows | Upload rows with missing or non-numeric quality | Job fails or skips with a readable message, no hang *(explore first)* | REQ-013 | P1 |
| TC-API-015 | Wrong datatype input | Invoke with a non-tabular dataset (e.g. txt) | Rejected or fails cleanly with clear error *(explore first)* | REQ-013 | P2 |
| TC-API-016 | Empty dataset | Invoke with a 0-byte input | Defined behaviour, no hang, outputs empty or error stated *(explore first)* | REQ-015 | P1 |
| TC-API-017 | Header-only dataset | Input with zero data rows | No crash; empty outputs *(explore first)* | REQ-015 | P2 |
| TC-API-018 | Repeat invocation | Invoke twice, same input | Two independent invocations, identical outputs | REQ-014 | P2 |
| TC-API-019 | Concurrent invocations | Invoke 3 at once, different inputs | Each output matches its own input, no cross-contamination | REQ-014 | P2 |
| TC-API-020 | Invocation response schema | Validate invocation and job JSON against expected schema | Required fields present with correct types | REQ-004 | P2 |
| TC-API-021 | Cross-user access | Second user requests first user's history/dataset | 403/404 | REQ-019 | P2 |
| TC-API-022 | Cleanup | After the session, list histories/workflows with the QA prefix | None remain | REQ-020 | P2 |
| TC-API-023 | Timing budget | Measure invoke-to-complete on fixture | Under agreed budget (set after baselining) | REQ-018 | P3 |
| TC-API-024 | Nonexistent workflow | Invoke with a bogus workflow id | 4xx with clear error, no server error | REQ-013 | P3 |

## 3. UI end-to-end tests (Playwright)

| ID | Title | Steps | Expected | Req | Pri |
|---|---|---|---|---|---|
| TC-UI-001 | Login | Sign in through the login page, save storage state | Authenticated landing page | REQ-009 | P1 |
| TC-UI-002 | Login failure | Wrong password | Error shown, not logged in | REQ-012 | P2 |
| TC-UI-003 | Upload via UI | Upload `reads.tabular` using the upload dialog | History item appears and reaches the green/ok state | REQ-001, REQ-002 | P1 |
| TC-UI-004 | Datatype shown | Expand the dataset | Format displayed as `tabular` | REQ-001 | P2 |
| TC-UI-005 | Workflow listed | Open the workflow list | Imported workflow visible by name | REQ-003 | P1 |
| TC-UI-006 | Launch run | Open the workflow, select the uploaded dataset, run | Run starts, confirmation shown | REQ-009 | P1 |
| TC-UI-007 | Follow progress | Watch the history during the run | Items move through queued/running to ok (explicit waits, no sleeps) | REQ-010 | P1 |
| TC-UI-008 | Outputs visible | After completion | Three labelled outputs present in the history | REQ-010 | P1 |
| TC-UI-009 | Output content in UI | Open `protein_counts` | Content matches golden | REQ-007, REQ-008 | P1 |
| TC-UI-010 | Invocation view | Open the workflow invocation page | Shows scheduled/complete and all steps green | REQ-010 | P2 |
| TC-UI-011 | UI vs API agreement | Run via UI, fetch the same invocation via API | States and output content agree | REQ-011 | P1 |
| TC-UI-012 | Failing run in UI | Run with malformed input | Failed item shown red with a readable error | REQ-013 | P1 |
| TC-UI-013 | Empty input in UI | Run with an empty dataset | Defined, visible outcome *(explore first)* | REQ-015 | P2 |
| TC-UI-014 | Required input validation | Try to launch without selecting an input | Launch blocked with clear message | REQ-009 | P2 |
| TC-UI-015 | Failure evidence | Force a failure | Trace, screenshot and video captured by the suite | REQ-020 | P3 |

## 4. Workflow editor (Playwright, highest flake risk)

| ID | Title | Steps | Expected | Req | Pri |
|---|---|---|---|---|---|
| TC-ED-001 | Build workflow in editor | Create workflow, add input, Filter, Sort, Count, connect, label outputs, save | Save confirmed | REQ-016 | P2 |
| TC-ED-002 | Editor result verified via API | Fetch the saved workflow via API | Three tool steps, correct tool IDs, connections, filter expression `c3>=20` | REQ-016, REQ-003 | P2 |
| TC-ED-003 | Editor-built workflow runs | Invoke the editor-built workflow | Output matches golden | REQ-016, REQ-008 | P3 |
| TC-ED-004 | Unsaved change warning | Edit, then navigate away | Warning shown *(explore first)* | REQ-016 | P3 |

## 5. Non-functional

| ID | Title | Steps | Expected | Req | Pri |
|---|---|---|---|---|---|
| TC-NF-001 | Accessibility: workflow run page | Run an axe scan | No critical or serious violations (or documented exceptions) | REQ-017 | P2 |
| TC-NF-002 | Accessibility: history panel | Run an axe scan | As above | REQ-017 | P3 |
| TC-NF-003 | Keyboard launch | Launch a run using the keyboard only | Possible, focus order sensible | REQ-017 | P3 |
| TC-NF-004 | Performance budget | Time the full UI run on the fixture | Within budget, trend recorded in CI | REQ-018 | P3 |
| TC-NF-005 | Dependency audit | Run `pip-audit` on test dependencies | No known critical vulnerabilities | REQ-020 | P3 |
| TC-NF-006 | Secrets hygiene | Scan repo for API keys | None committed; `.env` ignored | REQ-020 | P2 |

## 6. Deliberate defect demonstration

| ID | Title | Steps | Expected | Req | Pri |
|---|---|---|---|---|---|
| TC-DEF-001 | Threshold regression | On a branch, change `c3>=20` to `c3>20` | TC-API-006 and TC-API-009 fail; defect report written in `docs/defects/DEF-001.md` | REQ-005 | P2 |
| TC-DEF-002 | Sort order regression | Change sort to ascending | TC-API-007 fails | REQ-006 | P3 |

## Coverage summary

| Layer | Count | P1 | P2 | P3 |
|---|---|---|---|---|
| Smoke | 4 | 4 | 0 | 0 |
| API | 24 | 11 | 9 | 4 |
| UI E2E | 15 | 9 | 5 | 1 |
| Editor | 4 | 0 | 2 | 2 |
| Non-functional | 6 | 0 | 3 | 3 |
| Defect demo | 2 | 0 | 1 | 1 |
| **Total** | **55** | **24** | **20** | **11** |

## Suggested implementation order

1. TC-SMK-001 to 004
2. TC-API-001 to 008 (the core happy path, which also forms the oracle for everything else)
3. TC-UI-001 to 011
4. Negative and boundary cases (TC-API-009 to 017, TC-UI-012 to 014)
5. Non-functional, editor and defect demo

## Out of scope

- Real nanopore or protein data, and Portal Biotech's pipeline
- Galaxy's external data-source tools (network dependent)
- Load and stress testing beyond a single-fixture timing budget
- Multi-browser matrix (Chromium only; documented as a risk)
