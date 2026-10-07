import ast
import hashlib
import json
from pathlib import Path
import pytest

URL = "https://raw.githubusercontent.com/publisher/documents/" + "a" * 40 + "/notice.txt"
TEXT = "Write to editor@publisher.test for correspondence. Example: user@example.com is a placeholder."


def addr(value):
    return "0x" + value.hex() if isinstance(value, bytes) else str(value)


def mock(vm, text=TEXT, labels=None, status=200):
    vm.clear_mocks()
    raw = text.encode() if isinstance(text, str) else text
    vm.mock_web(r".*notice\.txt", {"status": status, "body": raw})
    vm.mock_llm(r"(?s).*Classify contextual email occurrences.*", json.dumps({"labels": labels if labels is not None else ["CONTACT", "EXAMPLE"]}))
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def contract(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.warp("2026-10-07T00:00:00Z")
    return direct_deploy("contracts/ContextualMaskStore.py")


def test_masked_output_and_bound_chunk(contract, direct_vm, direct_alice):
    source_hash = mock(direct_vm)
    contract.mask_source("one", URL, source_hash)
    report = contract.get_attempt(addr(direct_alice), "one")
    artifact = contract.get_artifact(source_hash)
    assert report["state"] == "READY"
    assert "editor@publisher.test" not in artifact["text"]
    assert "[contact-email]" in artifact["text"] and "user@example.com" in artifact["text"]
    assert hashlib.sha256(artifact["text"].encode()).hexdigest() == artifact["output_hash"]
    assert contract.read_chunk(source_hash, artifact["output_hash"], 0, 1024) == artifact["text"]
    assert report["candidates"][0]["start"] == TEXT.index("editor@publisher.test")


def test_example_preserved(contract, direct_vm):
    text = "The address user@example.com is a fictional example."
    source_hash = mock(direct_vm, text, ["EXAMPLE"])
    contract.mask_source("one", URL, source_hash)
    assert contract.get_artifact(source_hash)["text"] == text


def test_unknown_withholds_entire_artifact(contract, direct_vm, direct_alice):
    source_hash = mock(direct_vm, labels=["UNKNOWN", "EXAMPLE"])
    contract.mask_source("one", URL, source_hash)
    report = contract.get_attempt(addr(direct_alice), "one")
    assert report["state"] == "WITHHELD" and report["output"] == ""
    with direct_vm.expect_revert("no rendered artifact"):
        contract.get_artifact(source_hash)


def test_fake_hash_cannot_poison_real_artifact(contract, direct_vm, direct_alice):
    source_hash = mock(direct_vm)
    contract.mask_source("fake", URL, "0" * 64)
    assert contract.get_attempt(addr(direct_alice), "fake")["reason"] == "HASH_MISMATCH"
    contract.mask_source("real", URL, source_hash)
    assert contract.get_artifact(source_hash)["source_hash"] == source_hash


def test_replay_rejected(contract, direct_vm):
    source_hash = mock(direct_vm)
    contract.mask_source("one", URL, source_hash)
    with direct_vm.expect_revert("spent attempt"):
        contract.mask_source("one", URL, source_hash)


def test_caller_namespace(contract, direct_vm, direct_alice, direct_bob):
    source_hash = mock(direct_vm)
    contract.mask_source("same", URL, source_hash)
    direct_vm.sender = direct_bob
    contract.mask_source("same", URL, source_hash)
    assert contract.get_attempt(addr(direct_bob), "same")["spec"]["caller"].lower() == addr(direct_bob).lower()
    assert contract.get_attempt(addr(direct_alice), "same")["spec"]["caller"].lower() == addr(direct_alice).lower()


def test_conflicting_rendering_never_overwrites(contract, direct_vm, direct_alice):
    source_hash = mock(direct_vm)
    contract.mask_source("one", URL, source_hash)
    artifact = contract.get_artifact(source_hash)
    mock(direct_vm, labels=["EXAMPLE", "EXAMPLE"])
    contract.mask_source("two", URL, source_hash)
    assert contract.get_attempt(addr(direct_alice), "two")["state"] == "CONFLICTED"
    assert contract.get_artifact(source_hash) == artifact


@pytest.mark.parametrize("labels", [[], ["CONTACT"], [True, "EXAMPLE"], ["ALLOWED", "EXAMPLE"], ["CONTACT", "EXAMPLE", "CONTACT"]])
def test_malformed_labels_abort(contract, direct_vm, labels):
    source_hash = mock(direct_vm, labels=labels)
    with direct_vm.expect_revert("malformed label vector"):
        contract.mask_source("one", URL, source_hash)


@pytest.mark.parametrize("text,status,reason", [("error", 404, "HTTP_ERROR"), (b"\xff", 200, "INVALID_UTF8"), ("a" * 16385, 200, "TOO_LARGE"), ("", 200, "INVALID_TEXT"), ("hello\x00", 200, "INVALID_TEXT")], ids=["http-error", "invalid-utf8", "oversized", "empty", "nul"])
def test_unusable_body_withheld(contract, direct_vm, direct_alice, text, status, reason):
    source_hash = mock(direct_vm, text, [], status)
    contract.mask_source("one", URL, source_hash)
    assert contract.get_attempt(addr(direct_alice), "one")["reason"] == reason


def test_candidate_limit(contract, direct_vm, direct_alice):
    text = " ".join(f"user{i}@example.com" for i in range(17))
    source_hash = mock(direct_vm, text, [])
    contract.mask_source("one", URL, source_hash)
    assert contract.get_attempt(addr(direct_alice), "one")["reason"] == "TOO_MANY_CANDIDATES"


def test_chunk_binding_and_range(contract, direct_vm):
    source_hash = mock(direct_vm)
    contract.mask_source("one", URL, source_hash)
    artifact = contract.get_artifact(source_hash)
    with direct_vm.expect_revert("output binding mismatch"):
        contract.read_chunk(source_hash, "0" * 64, 0, 100)
    for offset, length in [(-1, 100), (0, 0), (0, 1025), (99999, 100)]:
        with direct_vm.expect_revert("invalid chunk range"):
            contract.read_chunk(source_hash, artifact["output_hash"], offset, length)


def test_no_candidates_preserves_source(contract, direct_vm):
    source_hash = mock(direct_vm, "A public document without email candidates.", [])
    contract.mask_source("one", URL, source_hash)
    assert contract.get_artifact(source_hash)["output_hash"] == source_hash


def test_caller_limit(contract, direct_vm):
    source_hash = mock(direct_vm, "No emails.", [])
    for index in range(32):
        contract.mask_source(str(index), URL, source_hash)
    with direct_vm.expect_revert("caller limit"):
        contract.mask_source("overflow", URL, source_hash)


def test_report_and_event_roots(contract, direct_vm, direct_alice):
    source_hash = mock(direct_vm)
    contract.mask_source("one", URL, source_hash)
    contract.mask_source("two", URL, source_hash)
    for value in [contract.get_artifact(source_hash), contract.get_attempt(addr(direct_alice), "one")] + contract.history(0, 20):
        root = value.pop("root")
        assert root == hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    events = contract.history(0, 20)
    assert events[1]["previous"] == events[0]["root"]


def helpers():
    tree = ast.parse(Path("contracts/ContextualMaskStore.py").read_text())
    tree.body = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.Assign)) or isinstance(node, ast.Import)]
    scope = {}
    exec(compile(tree, "helpers", "exec"), scope)
    return scope


def test_equivalence_substantive_fields():
    equivalent = helpers()["equivalent"]
    base = {"state": "READY", "labels": ["CONTACT"], "hash": "a", "output_hash": "b"}
    assert equivalent(base, dict(base))
    for field, value in [("labels", ["EXAMPLE"]), ("state", "WITHHELD"), ("hash", "c"), ("output_hash", "d")]:
        assert not equivalent(base, {**base, field: value})


def test_source_restrictions(contract, direct_vm):
    for url in ["http://localhost/file", "https://raw.githubusercontent.com/a/b/main/file.txt", URL + "?token=x", URL.replace("notice.txt", "../notice.txt"), "https://user@www.rfc-editor.org/rfc/rfc2606.txt"]:
        with direct_vm.expect_revert("invalid source binding"):
            contract.mask_source("one", url, "a" * 64)


def test_deterministic_span_integrity():
    scope = helpers()
    text = "Unicode prefix: αβ. user@example.com."
    matches = scope["candidates"](text)
    assert scope["render"](text, matches, ["CONTACT"]) == "Unicode prefix: αβ. [contact-email]."
    assert scope["render"](text, matches, ["UNKNOWN"]) is None
    matches[0]["start"] = 0
    assert scope["render"](text, matches, ["CONTACT"]) is None
