"""Offline, explicit revisions; local edits do not certify personal fidelity."""
import copy

from .card import canonical, digest, string
from .profile import make_profile, source_hashes, validate_answer, validate_profile, validate_sources


def checkout(profile):
    validate_profile(profile)
    return copy.deepcopy({"base.private.json": profile,
            "sources.private.json": profile["sources"],
            "answer.private.json": {"claims": profile["claims"], "unknowns": profile["unknowns"]},
            "INSTRUCTIONS.txt": (
                "Edit answer.private.json to correct claims, scope, conditions, exceptions, evidence and unknowns.\n"
                "Every claim must still cite an exact user-role quote. To add new evidence, append explicitly selected\n"
                "messages to sources.private.json with new IDs and correct roles. Existing sources are immutable.\n"
                "Assistant or editor commentary is not user endorsement. Do not edit base.private.json.\n"
                "Apply with: runaway profile revise base.private.json --answer answer.private.json "
                "--sources sources.private.json --reason 'Describe the correction' --out NEW_DIRECTORY\n"
                "All files are private. Revisions remain candidate_unvalidated; no model or remote service is called.\n")})


def changes(before, after):
    validate_profile(before)
    validate_profile(after)
    left = {c["id"]: c for c in before["claims"]}
    right = {c["id"]: c for c in after["claims"]}
    old_hashes, new_hashes = before["source_hashes"], after["source_hashes"]
    return {"before_profile_id": before["id"], "after_profile_id": after["id"],
            "direct_revision": after["previous_profile_id"] == before["id"],
            "added_claims": [c for cid, c in right.items() if cid not in left],
            "removed_claims": [c for cid, c in left.items() if cid not in right],
            "changed_claims": [{"id": cid, "fields": {key: {"before": old[key], "after": right[cid][key]}
                                  for key in old if old[key] != right[cid][key]}}
                               for cid, old in left.items() if cid in right and old != right[cid]],
            "claim_order_changed": list(left) != list(right),
            "unknowns": {"before": before["unknowns"], "after": after["unknowns"]},
            "added_source_ids": [sid for sid in new_hashes if sid not in old_hashes],
            "removed_source_ids": [sid for sid in old_hashes if sid not in new_hashes],
            "changed_source_ids": [sid for sid in old_hashes if sid in new_hashes and old_hashes[sid] != new_hashes[sid]],
            "note": "Local editorial revision; no authentication of editor identity or independent fidelity verification."}


def revise(previous, answer, sources, reason):
    validate_profile(previous)
    validate_sources(sources)
    string(reason, "revision reason", 16000)
    updated = source_hashes(sources)
    if any(updated.get(sid) != checksum for sid, checksum in previous["source_hashes"].items()):
        raise ValueError("Existing sources cannot be changed or removed in a revision; append new evidence with new IDs")
    validate_answer(answer, sources)
    if (answer == {"claims": previous["claims"], "unknowns": previous["unknowns"]}
            and sources == previous["sources"]):
        raise ValueError("No changes to claims, unknowns or sources")
    provenance = {"backend": "local_editor_revision", "model_requested": None,
                  "reason": reason, "answer_sha256": digest(canonical(answer)),
                  "note": "No model review carried forward. Local editor changes are not authenticated user endorsement."}
    result = make_profile(copy.deepcopy(answer), sources, provenance, previous)
    return result, changes(previous, result)
