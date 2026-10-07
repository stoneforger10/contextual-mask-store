# Security model

Experimental public-text rendering primitive. Do not use for secrets, regulated data or as a comprehensive PII sanitizer. The onchain report reveals original candidate values; rendered output is not confidentiality.

## Invariants

- Caller/attempt namespace and immutable attempt IDs prevent cross-caller substitution and report replay.
- Full acquired response must match SHA-256 before contextual classification; no caller-provided body or scores exist.
- Candidate spans are extracted deterministically and checked against source slices. Models supply labels, never spans or arbitrary replacement text.
- Each consequential label and the complete report are independently reproduced by validators; no threshold tolerance exists.
- UNKNOWN labels, unusable evidence and oversized inputs withhold publication. Malformed model output aborts consensus.
- Existing artifacts never change even if a later independently agreed rendering conflicts.
- Reads bind the exact source and output hashes; events are append-only, hash-linked and deployment-bound.

## Residual risks

Regex coverage is deliberately incomplete. AI can misclassify even unanimously; exact comparison can also hurt liveness. A caller can publish deceptive prose or prompt-injection material. A hash authenticates bytes, not publisher identity or truth. HTTPS redirects, upstream outages, censorship and document selection are not solved. Public Sybil callers can fill storage. No incentive economics or anti-spam deposits exist. A previously incorrect artifact cannot be repaired in place: use corrected source bytes or a separately reviewed policy deployment.

There are no assets, escrow, transfer approvals or cross-contract writes. No remediation/service delivery is certified. No independent security audit has been performed.

Report code issues privately to the repository owner before posting exploit details. Never include wallet keys, API tokens or confidential source documents.
