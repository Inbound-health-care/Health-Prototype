# Research — audit-trail / tamper-evident log standards (2026-06-11) — RESEARCH_ONLY

**Status: RESEARCH_ONLY.** Web research for **Stage 1 of ADR 0029** (governance audit trail +
deterministic monitor), per the new-phase discipline: search first, document, then build. Nothing
here is project truth until the Stage-1 tests prove the parts we adopt (`DOC_DISCIPLINE.md`
§Research gate). The decision record is **ADR 0030**; this note is the evidence behind it.

## What was checked and what holds (verdicts, with sources)

1. **Hash-chained tamper-evident logs.** Canonical construction unchanged:
   `entry_hash[i] = H(entry_hash[i-1] || canonical(entry[i]))`. SHA-256 remains the 2026 default
   (no practical attacks; collision ~2^128). Canonical references: RFC 6962 (Certificate
   Transparency Merkle logs; RFC 9162 v2.0 updates the tree structure, not the chain principle)
   and Ma & Tsudik 2008 (defines **truncation attacks**). NIST SP 800-92r1 is still a **draft**
   (IPD; not finalized as of 2026-06) and concerns log *management*, not construction.
   **Honest limits (must be documented in-module):** a plain chain detects in-place edits and
   re-orderings, but (a) **whole-file rewrite** with recomputed hashes and (b) **tail truncation**
   are only detectable against an **externally anchored head hash**. → ADOPT chain + an
   operator-publishable head; an HMAC-signed head was considered and **skipped** — this repo is
   zero-secret, and a key with nowhere to live is theater. The head anchor gives the same property
   when the operator records it outside the file (e.g., in a PR/commit).
2. **Canonical JSON.** The standard is RFC 8785 (JCS); not in the stdlib. The stdlib
   approximation `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)` is
   byte-deterministic **provided floats are excluded** (float repr is the known divergence; JCS
   number minimization differs). → ADOPT the stdlib form + **reject floats in event payloads by
   validation** (ints/strings/bools/None only). Skip the `rfc8785` PyPI package (a hard runtime
   dep for marginal gain).
3. **Healthcare audit-trail standards (concept-grounding, not compliance).**
   - HIPAA Security Rule **45 CFR 164.312(b)** "Audit controls": *"Implement hardware, software,
     and/or procedural mechanisms that record and examine activity in information systems that
     contain or use electronic protected health information."* Record + examine; integrity and
     review are the intent. The **HIPAA Security Rule NPRM (Jan 2025) is NOT final** as of
     2026-06 — current rule stands.
   - **ASTM E2147-18** (EHR audit logs): mandatory fields — user, date/time, event type, object,
     outcome; incorporated by reference into the ONC certification program.
   - **HL7 FHIR `AuditEvent`**: standard field vocabulary — `type`, `action`, `recorded`,
     `outcome`, `agent`, `entity`. → ADOPT as a **naming reference only** (this prototype is
     zero-PHI and local; no compliance claim).
4. **OWASP Logging Cheat Sheet (+ Top 10:2025 A09).** Exclude PHI/PII/values from logs; log
   **digests, rule IDs, and counts** instead of content; append-only storage; hash-chain for
   integrity; restrictive file permissions. → ADOPT strictly: the trail stores input/output
   SHA-256 digests + per-lens counts, **never note text or item values**. (Consistent with ADR
   0028's scanner printing no matched values.)
5. **Append-only JSONL in stdlib.** One canonical-JSON object per line carrying
   `prev_hash`/`entry_hash`; append with flush + `os.fsync` for durability; **single-writer
   only** (stdlib has no portable file lock — document, don't fake). Floats avoided (per #2).
   → ADOPT.

## What this changes vs the ADR 0029 sketch
Nothing structural. Two refinements: (a) the head-anchor (not HMAC) is the external-rewrite
defense, with the limit stated honestly; (b) payloads are digest+count-only (OWASP-strict) — the
trail proves *what was surfaced* by hash without duplicating surfaced text into a second file.

## Sources (primary where available)
- RFC 6962: https://www.rfc-editor.org/rfc/rfc6962.html · RFC 9162: https://datatracker.ietf.org/doc/html/rfc9162
- Ma & Tsudik, "A New Approach to Secure Logging": https://eprint.iacr.org/2008/185.pdf
- NIST SP 800-92r1 (draft): https://csrc.nist.gov/pubs/sp/800/92/r1/ipd
- RFC 8785 (JCS): https://datatracker.ietf.org/doc/html/rfc8785
- 45 CFR 164.312: https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.312
- HHS Security Rule NPRM status: https://www.hhs.gov/hipaa/for-professionals/security/hipaa-security-rule-nprm/index.html
- ASTM E2147-18: https://www.astm.org/Standards/E2147.htm
- HL7 FHIR AuditEvent: https://www.hl7.org/fhir/auditevent.html
- OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- OWASP Top 10:2025 A09: https://owasp.org/Top10/2025/A09_2025-Security_Logging_and_Alerting_Failures/
