# Data Classification

Every column in the database, and why it's stored the way it is. This answers issue H18. A test (`tests/unit/test_schema.py`) fails if a column isn't listed here, so a new column needs a decision.

## Encrypted columns

These end in `_enc` and hold AES-256-GCM ciphertext, encrypted per record (implemented in sub-phase 2.1).

| Column | Holds |
|---|---|
| `person.clinical_enc` | Sex and pregnancy status |
| `carrier_finding.payload_enc` | Gene, variant, classification, zygosity, inheritance, conditions |
| `couple.details_enc` | Self-reported relationship between partners |
| `invitation.relation_enc` | Which relative was invited |
| `care_case.reasons_enc` | Why the case has its priority |
| `message.content_enc` | Chat text |
| `case_note.body_enc` | Clinician's notes |
| `values_note.answers_enc` | What the person said matters to them |

## Unencrypted columns, with reasons

**Why these stay readable:** the database has to filter, sort or enforce rules on them, or they hold nothing personal. Every connection uses TLS in production, and disk encryption protects them at rest.

| Class | Meaning |
|---|---|
| Public | Published or directory content |
| Low | Reveals nothing about a person's health |
| Random | A random identifier |
| Pseudonym | An opaque or keyed identifier |
| Quasi-identifier | Could help identify someone in combination, so it's only reported in groups of 10 or more |
| Sensitive link | Connects a person to a record, but holds no result |
| Sensitive | Hints at health status, and is needed in the clear for the stated reason |

| Column | Class | Reason |
|---|---|---|
| `audit_log.seq` | Low | Chain position |
| `audit_log.at` | Low | Timestamp |
| `audit_log.actor` | Pseudonym | Login ID, needed for the access log |
| `audit_log.action` | Low | What happened, from a fixed vocabulary |
| `audit_log.resource` | Pseudonym | IDs only, needed for the access log |
| `audit_log.outcome` | Low | Allowed or denied |
| `audit_log.meta` | Low | Allowlisted scalar keys only, enforced in code |
| `audit_log.prev_hash` | Low | Chain link |
| `audit_log.hash` | Low | Chain link |
| `authz_outbox.id` | Random | Random UUID, meaningless on its own |
| `authz_outbox.operation` | Low | Pending change |
| `authz_outbox.subject` | Pseudonym | Internal person ID, or a grant ID |
| `authz_outbox.relation` | Low | Relation name |
| `authz_outbox.object` | Pseudonym | IDs only |
| `authz_outbox.expires_at` | Low | When the access runs out |
| `authz_outbox.attempts` | Low | Retry count |
| `authz_outbox.applied_at` | Low | Completion |
| `authz_outbox.created_at` | Low | Time of creation, needed for ordering and retention |
| `centre.id` | Random | Random UUID, meaningless on its own |
| `centre.pack_code` | Public | Public directory |
| `centre.region` | Public | Same |
| `centre.name` | Public | Same |
| `centre.services` | Public | Same |
| `centre.contact` | Public | Same |
| `centre.source_url` | Public | Same |
| `centre.checked_on` | Public | Same |
| `event.id` | Random | Random UUID, meaningless on its own |
| `event.subject` | Pseudonym | Keyed hash of the person's ID |
| `event.kind` | Low | From a fixed allowlist |
| `event.pack_code` | Low | Strata |
| `event.lang` | Low | Strata |
| `event.literacy` | Low | Strata |
| `event.region` | Quasi-identifier | Strata; reported at 10 or more only |
| `event.age_band` | Quasi-identifier | Same |
| `event.gender` | Quasi-identifier | Same |
| `event.value` | Low | A number with no free text |
| `event.at` | Low | Timestamp |
| `kb_chunk.id` | Random | Random UUID, meaningless on its own |
| `kb_chunk.pack_code` | Public | Published education content |
| `kb_chunk.condition_id` | Public | Same |
| `kb_chunk.lang` | Public | Same |
| `kb_chunk.level` | Public | Same |
| `kb_chunk.text` | Public | Same |
| `kb_chunk.source_url` | Public | Same |
| `kb_chunk.status` | Public | Same |
| `kb_chunk.reviewed_by` | Low | Reviewer's name, a professional record |
| `kb_chunk.content_version` | Public | Same |
| `kb_chunk.embedding` | Public | Derived from public text |
| `kb_chunk.created_at` | Low | Time of creation, needed for ordering and retention |
| `person.id` | Random | Random UUID, meaningless on its own |
| `person.keycloak_sub` | Pseudonym | Opaque login ID, needed to find the person on every request |
| `person.national_id_hash` | Pseudonym | Keyed HMAC of the national ID, needed to match lab reports. Not reversible without the key |
| `person.pack_code` | Low | Which country's rules apply |
| `person.preferred_lang` | Low | Needed to serve content |
| `person.literacy_level` | Low | Needed to serve content |
| `person.region` | Quasi-identifier | Equity reporting required by R6. Only leaves the database in aggregates of 10 or more |
| `person.age_band` | Quasi-identifier | Equity reporting. A band, never a birth date |
| `person.gender` | Quasi-identifier | Equity reporting, and harm monitoring |
| `person.service_consent_at` | Low | Must be checked before showing any genetic data |
| `person.results_withheld_at` | Sensitive link | The person chose not to know. It must be readable to withhold results, and says nothing about what they are |
| `person.created_at` | Low | Time of creation, needed for ordering and retention |
| `assessment.id` | Random | Random UUID, meaningless on its own |
| `assessment.person_id` | Sensitive link | Pairs before and after scores |
| `assessment.instrument` | Low | Which quiz |
| `assessment.phase` | Low | Before or after |
| `assessment.lang` | Low | Equity reporting |
| `assessment.score` | Sensitive | Comprehension score, needed for R6 aggregates |
| `assessment.created_at` | Low | Time of creation, needed for ordering and retention |
| `conversation.id` | Random | Random UUID, meaningless on its own |
| `conversation.person_id` | Sensitive link | Shows only that someone used chat |
| `conversation.lang` | Low | Needed to serve content |
| `conversation.created_at` | Low | Time of creation, needed for ordering and retention |
| `couple.id` | Random | Random UUID, meaningless on its own |
| `couple.person_a` | Sensitive link | Needed to check membership on every couple request |
| `couple.person_b` | Sensitive link | Same |
| `couple.invite_code_hash` | Pseudonym | Keyed hash, so a stolen database can't be used to join a couple |
| `couple.invite_expires_at` | Low | Invite expiry |
| `couple.created_at` | Low | Time of creation, needed for ordering and retention |
| `genetic_report.id` | Random | Random UUID, meaningless on its own |
| `genetic_report.person_id` | Sensitive link | Shows a person has a report, which everyone screened does. Needed to fetch their own findings |
| `genetic_report.source_lab` | Low | Trust and traceability |
| `genetic_report.source_report_id` | Pseudonym | Lab's reference, needed so replays are harmless |
| `genetic_report.report_version` | Low | Amended results |
| `genetic_report.superseded_at` | Low | Amended results |
| `genetic_report.panel_version` | Low | Which genes were tested, needed for residual risk |
| `genetic_report.bundle_sha256` | Low | Integrity check on what was received |
| `genetic_report.attestation` | Low | Matching reads trusted reports only |
| `genetic_report.received_at` | Low | Start of the time-to-referral measure |
| `invitation.id` | Random | Random UUID, meaningless on its own |
| `invitation.sender_id` | Sensitive link | Enforces the daily limit, and is never returned to a recipient unless the sender opts in |
| `invitation.token_hash` | Pseudonym | Keyed hash, so a stolen database can't be used to redeem links |
| `invitation.disclose_identity` | Low | The sender's choice |
| `invitation.expires_at` | Low | Expiry |
| `invitation.redeemed_at` | Low | Single use |
| `invitation.created_at` | Low | Time of creation, needed for ordering and retention |
| `care_case.id` | Random | Random UUID, meaningless on its own |
| `care_case.subject_id` | Sensitive link | Needed for a person's own journey |
| `care_case.couple_id` | Sensitive link | Links partners' follow-up |
| `care_case.counsellor_id` | Low | The assignment, needed for the queue |
| `care_case.priority` | Sensitive | Queue ordering has to sort on this in the database. It hints at seriousness, but not why. The reasons are encrypted |
| `care_case.state` | Sensitive | Queue and stall detection query on this |
| `care_case.step_due` | Low | Deadline, queried by the stall scan |
| `care_case.stalled` | Low | Alerting |
| `care_case.version` | Low | Optimistic lock |
| `care_case.created_at` | Low | Time of creation, needed for ordering and retention |
| `carrier_finding.id` | Random | Random UUID, meaningless on its own |
| `carrier_finding.report_id` | Sensitive link | Number of rows shows how many findings a report has. Accepted for now; see limits below |
| `consent.id` | Random | Random UUID, meaningless on its own |
| `consent.grantor_id` | Sensitive link | Needed to list a person's own consents |
| `consent.grantee_id` | Sensitive link | Needed to enforce the share |
| `consent.couple_id` | Sensitive link | Needed to enforce match consent |
| `consent.kind` | Low | Drives enforcement |
| `consent.reveal_level` | Low | The most private choice wins, so it must be readable |
| `consent.purpose` | Low | Recorded purpose of the share |
| `consent.terms_version` | Low | Which wording was agreed to |
| `consent.expires_at` | Low | Enforcement |
| `consent.revoked_at` | Low | Enforcement |
| `consent.created_at` | Low | Time of creation, needed for ordering and retention |
| `message.id` | Random | Random UUID, meaningless on its own |
| `message.conversation_id` | Sensitive link | Threading |
| `message.role` | Low | User or assistant |
| `message.boundary` | Sensitive | AI safety metrics and audit, R3. Shows the category of a question, never its text |
| `message.source` | Low | LLM or template |
| `message.validator_flags` | Low | Names of rules that fired, never text |
| `message.created_at` | Low | Time of creation, needed for ordering and retention |
| `appointment.id` | Random | Random UUID, meaningless on its own |
| `appointment.counsellor_id` | Low | Calendar |
| `appointment.case_id` | Sensitive link | Links a booking to a case |
| `appointment.starts_at` | Low | Calendar |
| `appointment.ends_at` | Low | Calendar |
| `appointment.mode` | Low | Calendar |
| `appointment.lang` | Low | Calendar |
| `appointment.status` | Low | Calendar |
| `appointment.created_at` | Low | Time of creation, needed for ordering and retention |
| `break_glass_event.id` | Random | Random UUID, meaningless on its own |
| `break_glass_event.actor_id` | Low | Who broke the glass |
| `break_glass_event.case_id` | Sensitive link | Which case |
| `break_glass_event.reason` | Sensitive | Must be readable by reviewers. Reviewers are told not to put health details here |
| `break_glass_event.expires_at` | Low | Time limit |
| `break_glass_event.reviewed_by` | Low | The reviewer |
| `break_glass_event.reviewed_at` | Low | Review tracking |
| `break_glass_event.created_at` | Low | Time of creation, needed for ordering and retention |
| `case_note.id` | Random | Random UUID, meaningless on its own |
| `case_note.case_id` | Sensitive link | Access control |
| `case_note.author_id` | Low | The clinician |
| `case_note.created_at` | Low | Time of creation, needed for ordering and retention |
| `pathway_step.id` | Random | Random UUID, meaningless on its own |
| `pathway_step.case_id` | Sensitive link | Traceability, R5 |
| `pathway_step.from_state` | Sensitive | Traceability, R5, and time to referral |
| `pathway_step.to_state` | Sensitive | Same |
| `pathway_step.actor` | Pseudonym | Who made the change |
| `pathway_step.fhir_ref` | Pseudonym | Reference only, holding no content |
| `pathway_step.at` | Low | Time to referral |
| `referral.id` | Random | Random UUID, meaningless on its own |
| `referral.case_id` | Sensitive link | Traceability, R5 |
| `referral.created_by` | Low | The clinician |
| `referral.kind` | Sensitive | Traceability, R5. Shows a referral type, never a result |
| `referral.destination` | Sensitive | Same |
| `referral.status` | Low | Tracking |
| `referral.fhir_ref` | Pseudonym | Reference only |
| `referral.created_at` | Low | Time of creation, needed for ordering and retention |
| `values_note.id` | Random | Random UUID, meaningless on its own |
| `values_note.person_id` | Sensitive link | Owner lookup |
| `values_note.shared_with_case_id` | Sensitive link | Records the person's choice to share |
| `values_note.created_at` | Low | Time of creation, needed for ordering and retention |

## Accepted limits

- **Number of findings:** the row count in `carrier_finding` shows how many reportable findings a report has. Removing that needs one encrypted document per report, which is worth considering after the prototype.
- **Case priority and state:** someone with direct database access can see that a case is P1 and at which step, but not why.
- **Who shares with whom:** `consent` and `couple` show relationships to anyone with direct database access, because access rules are enforced on them. Application code only ever returns a person's own rows.
- **Keys:** `LOCAL_KEK_B64` is for development and is refused in production.
