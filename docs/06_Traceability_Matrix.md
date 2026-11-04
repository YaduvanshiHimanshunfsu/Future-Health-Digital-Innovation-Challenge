# 06 — Traceability Matrix

Use this to cross-verify the whole project: each challenge requirement should trace to features, code, tests and a phase check. A blank at any step means a gap.

`[NEW]` marks items added by the [review](04_Project_Review_Issues_and_Improvements.md). Feature numbers come from `docs/03` §1, and screens from `docs/frontend.md` §4.

## Requirements

| Req | What's required | Features | Backend modules | Endpoints | Screens | Tests | Phase checks |
|---|---|---|---|---|---|---|---|
| **R1** | Plain, non-stigmatising risk explanation, including uncertainty and risk versus diagnosis | F1–F5 | `risk_engine`, `explain`, `kb` | `/me/results`, `/me/risk`, `/chat` | P7, P8, P9, P2 | `test_risk_engine`, `test_validators`, eval sets | V2.4.*, V2.5.*, V4.2.*, V6.1.* |
| **R2** | Access to screening, counselling and options, without coercion | F6–F8, F16 | `decision`, `centres` [NEW] | `/options`, `/values` [NEW], `/centres` [NEW] | P10, centres [NEW] | Options and values tests | V1.2.2, V4.4.*, V5.2.* |
| **R3** | Escalate to accredited professionals, with a clear boundary | F4, F9, F17–F19 | `explain/router`, `triage`, `booking` [NEW] | `/chat`, `/cases`, `/booking` [NEW] | P9, P14, P16, P17 | `test_router`, `test_triage`, `test_cases` | V4.3.*, V4.5.* |
| **R4** | Explicit consent, role-based access, minimisation, auditable sharing, individual control | F10–F13, F20 | `privacy/*`, `api/v1/shared` [NEW] | `/consents`, `/couples/*`, `/invitations`, `/me/access-log`, `/shared` [NEW] | P11, P12, P13 | `test_consents`, `test_matching`, `test_invitations`, `test_bola`, `test_crypto`, `test_audit_chain`, `test_redaction` | V2.1.*, V3.1.* to V3.5.* |
| **R5** | Traceable path from result to counselling, confirmatory test and specialist services | F14, F21 | `pathway`, `booking` [NEW], `notifications` | `/pathway/*`, `/booking` [NEW], `/referrals` [NEW] | P6, P14, P17 | `test_state_machine` | V5.1.*, V5.2.* |
| **R6** | Measured comprehension, uptake, time to referral, privacy and equity, with no single choice as the sole success measure | F15, F22–F25 | `assessments`, `analytics` | `/assessments`, `/analytics/metrics` | P15, P18, P19 | `test_fairness`, eval sets | V5.3.*, V5.4.*, V6.1.*, V6.2.* |

## R6 metrics and their data sources

Every metric the challenge asks for needs a source. These are the ones that had none, or a broken one, in the original spec.

| Metric | Source | Original spec problem | Check |
|---|---|---|---|
| Understanding | Paired teach-back events | Unpaired averages | V5.3.1, V6.2.* |
| Counselling uptake | Pathway steps, by priority | Escalated cases had no steps (H10) | V5.1.1, V5.4.2 |
| Time to appropriate referral | Steps from `RESULT_RELEASED` | Started from `COUNSELLING_REQUESTED`, and missed at-risk cases (H10) | V5.4.2 |
| Privacy: blocked attempts | Security events | Not recorded (H11) | V1.5.4, V3.1.2 |
| Privacy: revocation time | Timed revoke event | No source (H11) | V3.2.2 |
| Privacy: PII to LLM | Automated tests | Arabic not covered (H6) | V3.5.3–V3.5.5 |
| Equity: language and literacy | Strata on events | Calculation hid real gaps (H11) | V5.4.1 |
| Equity: age, gender, region | Strata on events | Age and gender not collected (H11) | V5.4.6 |
| AI safety | Stored validator flags | Flags discarded (H11) | V5.4.6 |

## Judging criteria

| Criterion | Evidence to show | Where it's produced |
|---|---|---|
| Health impact and clinical relevance | Clinician review, real comprehension test | 1.2, 2.4, 6.2 |
| Technical depth and architecture | Technical doc, test suites, threat model | 2, 3, 4, 6.4 |
| Working solution and demonstration quality | End-to-end journey, video | 5.5, 6.5 |
| Responsible AI, safety and data governance | Safety report, privacy tests, legal baseline | 1.2, 3, 4.2, 6.1, 6.3 |
| Scalability and deployment readiness | One-command stack, country pack swap, deployment section | 1.3, 2.6, 6.3, 6.4 |
| Commercial viability and path to pilot | Commercial and pilot plan | 6.4 |

## Issues to phases

See [phases/CROSS_VERIFICATION.md](phases/CROSS_VERIFICATION.md), which maps every issue to its sub-phase and check.
