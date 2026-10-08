# StudioNet proof ledger

## Deployment and exact source

- Contract: [0x6BdA7537FcE3Bf084A8f5ADB85B7Eaf6A70c6264](https://explorer-studio.genlayer.com/address/0x6BdA7537FcE3Bf084A8f5ADB85B7Eaf6A70c6264).
- Published source and fixture commit: `78d75851cf5263e46f76c0bd0e7e0d61a01df921`.
- Normalized deployed/local source SHA-256: `9f32e45d3e93171e24ebdd6ae82b729019486ac466c91bedd717e592f04d4358`. Comparison normalizes CRLF and the final newline, not source logic.
- Dedicated encrypted test-account public address: `0x7a413BB4AB62E31d62d4cD9efC8C8a8Dae37FB42`.
- No funded transfer, private-key export or mainnet deployment was performed.

## Verified receipt matrix

Each listed positive receipt was checked for `FINALIZED`, leader execution `SUCCESS` and `MAJORITY_AGREE`. Majority agreement is not unanimity. CLI banners alone are not evidence.

| Proof | Transaction | Readback / outcome |
| --- | --- | --- |
| Deployment | [349bba22…](https://explorer-studio.genlayer.com/tx/0x349bba228a1c2aa5e767df5dfca73337a8b0ab727ecc5c09e05ddcb3d1446780) | RPC deployed source matches the published contract. |
| Context-sensitive masking | [233f1637…](https://explorer-studio.genlayer.com/tx/0x233f16378857cb08391cbb9e82c49f011220ad7e905a549b26980d4c587c48b7) | `contact-demo`: `READY`; `CONTACT, EXAMPLE`; only the operational-use occurrence replaced. |
| Example preservation | [df771831…](https://explorer-studio.genlayer.com/tx/0xdf771831765fb3e99cf2cfb7d3321856e923d5b016da62bec09a0c8abb135139) | `illustration-demo`: `READY`; `EXAMPLE, EXAMPLE`; full text preserved. |

For both processing transactions, `scripts/verify_demo.mjs` checked the stored report root, artifact root, exact expected rendering, output hash and bound chunk read. The sources are synthetic publisher-authored fixtures. They demonstrate semantic transformation, not independently verified mailbox ownership, deliverability or authorship.

## Evidence and rendered hashes

| Fixture | Exact fetched source SHA-256 | Rendered SHA-256 |
| --- | --- | --- |
| [contact.txt](https://raw.githubusercontent.com/stoneforger10/contextual-mask-store/78d75851cf5263e46f76c0bd0e7e0d61a01df921/examples/contact.txt) | `622f9c95d4fb92fb4eb570a940f3478151a7ea308aa564b6c7bdd904d7de8c2c` | `9dc8267c8ebf1086b1a5bba8c330d51c7f676b1a95dbc26274b0aaac5bb7ab33` |
| [illustration.txt](https://raw.githubusercontent.com/stoneforger10/contextual-mask-store/78d75851cf5263e46f76c0bd0e7e0d61a01df921/examples/illustration.txt) | `f3569699dbdd1754d8c7716de3d77121e5493d0d7f209a5d7e9a48ee2618ee52` | `f3569699dbdd1754d8c7716de3d77121e5493d0d7f209a5d7e9a48ee2618ee52` |

The complete raw response, not a caller-supplied summary, reaches classification after hash checking. Models provide contextual labels, not replacement text or spans. Masked output remains public; attempt reports contain original candidate addresses. This is not confidential storage.

## Negative-test status and limits

An attempted all-zero wrong-hash CLI call finalized with leader `ERROR`, `MAJORITY_AGREE` and `[EXPECTED] invalid source binding`: [b0535676…](https://explorer-studio.genlayer.com/tx/0xb0535676cd95f15d1fef1cf9fc0bbd75cf0b9af28d5060c44813633cb3e3a423). It failed at input validation and is **not** evidence of the intended `HASH_MISMATCH → WITHHELD` transition. A nonnumeric wrong-hash retry did not start because permission review timed out. No retry transaction hash is claimed.

Replay rejection, wrong-hash withholding, UNKNOWN handling and conflicting-artifact immutability pass mocked direct tests. They are not claimed as completed onchain proofs. Exact equivalence helper tests are not a distributed validator-disagreement experiment. Malformed AI output or validator disagreement can abort consensus without storing an attempt; they are not falsely listed as recorded `CONFLICTED` outcomes.

## Reproduce verification

```powershell
npm ci
node scripts/check.mjs --source 0x6BdA7537FcE3Bf084A8f5ADB85B7Eaf6A70c6264
node scripts/check.mjs --success 0x349bba228a1c2aa5e767df5dfca73337a8b0ab727ecc5c09e05ddcb3d1446780
node scripts/check.mjs --success 0x233f16378857cb08391cbb9e82c49f011220ad7e905a549b26980d4c587c48b7
node scripts/check.mjs --success 0xdf771831765fb3e99cf2cfb7d3321856e923d5b016da62bec09a0c8abb135139
node scripts/verify_demo.mjs 0x6BdA7537FcE3Bf084A8f5ADB85B7Eaf6A70c6264 0x7a413BB4AB62E31d62d4cD9efC8C8a8Dae37FB42 contact-demo contact
node scripts/verify_demo.mjs 0x6BdA7537FcE3Bf084A8f5ADB85B7Eaf6A70c6264 0x7a413BB4AB62E31d62d4cD9efC8C8a8Dae37FB42 illustration-demo illustration
```

On Windows environments where Node HTTPS transport cannot reach StudioNet, prepend `--require ./scripts/windows_read_transport.cjs` after `node`. This read-only transport fallback uses native PowerShell for RPC; it does not sign or send transactions.

Direct tests: **25 passed**, using mocked HTTP/AI in leader-only direct execution. GenVM lint and SDK validation pass (one informational newer-runner notice). No independent security audit or production suitability is claimed.
