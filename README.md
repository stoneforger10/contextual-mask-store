# ContextualMaskStore

Source-bound contextual email masking and immutable, hash-addressed rendering for GenLayer. Experimental; not a privacy vault, universal PII detector, or audited production deployment.

## Live deployment

[StudioNet contract](https://explorer-studio.genlayer.com/address/0x6BdA7537FcE3Bf084A8f5ADB85B7Eaf6A70c6264). Deployed source matches commit `78d75851cf5263e46f76c0bd0e7e0d61a01df921`. See [LIVE_PROOFS.md](LIVE_PROOFS.md) for independently checked receipts and artifact readbacks, and [SUBMISSION.md](SUBMISSION.md) for contribution text. GenVM lint and SDK validation pass; 25 mocked direct tests pass. These tests do not establish distributed validator agreement or an independent security audit.

## Problem and consensus boundary

An email-shaped string can be an operational contact, a fictional syntax example, or an ambiguous reference. Blind regular-expression replacement destroys useful examples; blindly keeping them can leave operational contacts in the rendered text. A deterministic chain can find byte/character spans but cannot reliably interpret their use in prose.

The contract owns evidence acquisition, candidate enumeration, contextual decisions, deterministic rendering, artifact immutability and hash-bound reads. The caller owns only a URL, raw-response SHA-256 commitment and attempt ID. It cannot supply the source body, labels, spans, replacement text, scores or summaries. External publishers own the document, not the classifier's outcome.

```text
pinned public HTTPS source
  → independent full-body fetch and commitment verification
  → deterministic candidate spans
  → independent AI CONTACT / EXAMPLE / UNKNOWN vector
  → exact full-report validator agreement
  → deterministic CONTACT replacements, EXAMPLE preservation
  → immutable content-addressed artifact and bound chunk reads
```

Each validator independently fetches the document and reruns contextual classification. The exact candidate vector, labels, source hash, HTTP status, state, rendered text and output hash must agree. No score tolerance or leader-only schema validation controls publication. Malformed model output aborts consensus; valid UNKNOWN labels record WITHHELD without an artifact. Validator disagreement does not commit a report or publish output; it is not falsely represented as a stored CONFLICTED report.

## State and architecture

```text
mask_source
  ├─ unavailable / changed / oversized / ambiguous → WITHHELD
  ├─ known labels, no previous rendering          → READY + artifact
  ├─ identical previous rendering                → READY, reuse artifact
  └─ different previous rendering                → CONFLICTED, preserve artifact
```

Attempt reports are keyed by authenticated caller and attempt ID. Artifacts are keyed by exact source-body SHA-256 under this deployment's fixed policy. Append-only events link report roots; artifacts cannot be edited, revoked, reset or replaced. Readers bind BOTH source and rendered-output hashes; a mistaken output reference cannot silently return different content. Masks replace exact occurrence spans with `[contact-email]`; surrounding text and EXAMPLE occurrences remain unchanged. Models never generate the rendered document.

This is not the prior owner-controlled graph mechanism: there is no owner, proposal approval, graph edge, parent version or graph head. It is also not the evidence-certification/one-time-consumption mechanism: the product is a reusable rendered string, not a certificate or execution capability. The consequential nondeterministic output is the occurrence classification that changes the rendered artifact itself. One representative implementation is provided, not parallel domain variants. Acceptance and universal novelty are not claimed.

## Scope and safety

- Only ordinary, unquoted ASCII email candidates recognized by the documented regex are covered. Internationalized, obfuscated, quoted-local-part and otherwise unmatched addresses are outside scope. Phones, names and other PII are not covered.
- CONTACT means the document uses the occurrence as operational or author correspondence. It does not establish mailbox ownership, deliverability, identity or real-world authenticity. EXAMPLE preserves illustrative/test addresses and reserved example domains.
- The reserved example-domain policy is grounded in [RFC 2606](https://www.rfc-editor.org/rfc/rfc2606.html). The model must still interpret the document's context; recognizing an address-shaped string alone never determines CONTACT.
- All inputs, candidate values, reports and output are PUBLIC. The candidate list itself contains the original address. Neither masking nor omission of the raw document creates onchain confidentiality. Never submit private data; use client-side encryption and private processing when privacy is required.
- AI errors and prompt injection remain possible. UNKNOWN withholds output but a confidently wrong label can still pass consensus. Use independent review for sensitive publication.
- HTTPS sources are restricted to commit-pinned raw GitHub `.txt` files and RFC Editor text documents. Redirects are not independently attested; raw-body commitments bind the acquired bytes. There is no claim of publisher independence or authenticated authorship.
- Maximum 16 KiB full response, 16 candidates, 32 attempts per caller and 1 KiB character chunks. These bounds constrain compute but do not prevent Sybil spam.
- Sources are immutable evidence snapshots, not assertions about current web content. Reports record acquisition time; consumers must choose their own maximum acceptable age. Reusing an artifact does not refresh its provenance or erase its old report.
- No payments, balance accounting, external writes, generated code execution, wallet keys, tokens or settlement exist inside this contract.

## API

`mask_source(attempt_id, url, expected_hash)`

`get_attempt(caller, attempt_id)`, `get_artifact(source_hash)`, `read_chunk(source_hash, output_hash, offset, length)`, `history(offset, limit)`.

Get the READY artifact's `output_hash` and bind it on every chunk read. Offsets/lengths are Python Unicode character counts, not UTF-8 byte offsets.

## Example workflows

`examples/contact.txt` is a synthetic publishing notice with one operational-use address and one placeholder. Expected output masks only the former. `examples/illustration.txt` contains two fictional examples; expected output preserves both. They are publisher-authored test artifacts, not independent observations of mailbox ownership or identities. Publish them and pin URLs to the source commit before processing.

A deliberately wrong body hash must produce WITHHELD. A spent caller/attempt ID must revert. Reclassification of an existing body into a different rendered text must never overwrite the original artifact.

## Install and test

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/genvm-lint check contracts/ContextualMaskStore.py --json
.venv/Scripts/python -m pytest tests -q
npm ci
```

Direct tests use mocked HTTP/AI and run the leader only. A helper comparison test checks equivalence decisions, not distributed validators. Live coverage is listed separately in LIVE_PROOFS.md. The narrow Windows cleanup fixture defers unlinking only the test framework's open temporary message file; it does not skip execution or assertions.

## StudioNet deployment

```powershell
genlayer network set studionet
genlayer account use YOUR_ENCRYPTED_KEYSTORE
genlayer deploy --contract contracts/ContextualMaskStore.py
genlayer write ADDRESS mask_source --args example1 PINNED_PUBLIC_URL RAW_BODY_SHA256
genlayer call ADDRESS get_attempt --args CALLER_ADDRESS example1
genlayer call ADDRESS get_artifact --args RAW_BODY_SHA256
genlayer call ADDRESS read_chunk --args RAW_BODY_SHA256 OUTPUT_SHA256 0 1024
```

Calculate SHA-256 from the complete raw response bytes, not normalized text or a GitHub JSON wrapper. StudioNet is an experimental gasless environment. Verify every receipt's execution outcome and majority agreement, not the CLI success banner or FINALIZED status alone. Compare deployed source with the exact GitHub contract revision. An expected execution error is a negative test, not a successful state transition.

See SECURITY.md, LIVE_PROOFS.md and SUBMISSION.md. No guaranteed points, approval, privacy or audit status is represented.
