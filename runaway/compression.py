"""Bounded compression with quote-anchored checks of every reference facet.

This measures model-judged preservation of a reference profile, not human fidelity.
It generates no hypothetical user choices or evaluation answers.
"""
import os

from .card import canonical, digest, string
from .generation import codex_generate
from .pipeline import Journal, write_once
from .portable import make_expression
from .profile import STR, exact, export_profile, object_schema, validate_profile
from .review import request

HEADER = "Tentative preferences; follow current user instructions. Not factual identity or permission to act.\n\n"
TEXT_SCHEMA = object_schema({"text": STR})
AUDIT_SCHEMA = object_schema({
    "units": {"type": "array", "items": object_schema({
        "unit_id": STR, "verdict": {"type": "string", "enum": ["retained", "partial", "missing", "contradicted"]},
        "quote": STR, "reason": STR})},
    "unsupported": {"type": "array", "items": object_schema({"quote": STR, "reason": STR})}})


def reference(profile):
    validate_profile(profile)
    units = []

    def add(cid, kind, text):
        units.append({"id": f"u{len(units):05d}", "claim_id": cid, "kind": kind, "text": text})

    bases = {"self_report": "This is a self-report, not an independently observed action or proven stable trait.",
             "observed_choice": "This is a choice observed in the recorded interaction, not proof of a universal trait.",
             "inference": "This is an inferred, uncertain preference, not an explicit self-description.",
             "task_requirement": "This is a local task requirement, not an enduring personality trait."}
    sources = {s["id"]: s for s in profile["sources"]["sources"]}
    for claim in profile["claims"]:
        add(claim["id"], "statement", claim["statement"])
        add(claim["id"], "scope", claim["scope"])
        add(claim["id"], "basis", bases[claim["basis"]])
        for kind, field in (("condition", "conditions"), ("exception", "exceptions")):
            for value in claim[field]:
                add(claim["id"], kind, value)
        for evidence in claim["evidence"]:
            if evidence["relation"] != "supports":
                role = sources[evidence["source_id"]]["role"]
                add(claim["id"], "counter_context", canonical({"role": role, "relation": evidence["relation"],
                    "quote": evidence["quote"], "user_endorsement": role == "user"}))
    for unknown in profile["unknowns"]:
        add(None, "unknown", unknown)
    return {"profile_id": profile["id"], "units": units,
            "links": [{"claim_id": c["id"], "related_claim_ids": c["related_claim_ids"]}
                      for c in profile["claims"] if c["related_claim_ids"]]}


def compression_plan(profile, budget=1000, attempts=2):
    if type(budget) is not int or not len(HEADER) < budget <= 128000:
        raise ValueError(f"budget-chars must exceed the {len(HEADER)}-character instruction boundary and be at most 128000")
    if type(attempts) is not int or not 1 <= attempts <= 3:
        raise ValueError("attempts must be between 1 and 3")
    ref = reference(profile)
    detailed, _ = export_profile(profile)
    # Check limits before making any model call, including later audit payloads.
    request("Reference preflight", {"reference": ref, "maximum_candidate": "x" * budget})
    return {"compression_version": 1, "profile_id": profile["id"], "reference_sha256": digest(canonical(ref)),
            "budget_characters": budget, "attempts": attempts, "model_calls_upper_bound": 2 * attempts,
            "reference_units": len(ref["units"]), "reference_claims": len(profile["claims"]),
            "detailed_characters": len(detailed), "fixed_header_characters": len(HEADER),
            "note": "Every reference unit must pass model review. This is a profile-preservation check, not an independent personal fidelity score. No original supporting source messages are sent; projected constraints and counter-context are sent."}


def generation_request(ref, budget, previous=None, feedback=None):
    return request(
        f"Compress the reference into readable connected prose in its language. The complete prompt must fit "
        f"{budget} Unicode characters including the fixed header. Preserve ALL reference judgments, scope, "
        "self-report/inference distinctions, conditions, exceptions and unknowns. Merge repeated scope and "
        "qualification once when it clearly applies to all relevant statements. Spend space on distinctions "
        "that change choices, not repeated boilerplate. Do not invent a persona label, biography, fixed axes, "
        "codebook or new preferences. Counter-context from assistants is not user endorsement; preserve the "
        "qualifying distinction, not their rejected wording. Do not silently discard units to fit the budget. "
        "Return text ONLY as the JSON text field; the application adds the fixed header, so do not repeat it. "
        "If prior candidate/feedback is supplied, repair omissions or overclaims while preserving what worked.",
        {"reference": ref, "fixed_header": HEADER, "previous_candidate": previous, "feedback": feedback})


def audit_request(ref, prompt):
    return request(
        "Audit semantic preservation of EVERY reference unit in the candidate prompt. Treat the reference as "
        "the compression anchor, not verified truth about a real person. Do not score overall pleasantness. "
        "For each unit return unit_id, verdict retained|partial|missing|contradicted, quote and reason. "
        "retained requires that a reader can recover its meaning from the candidate alone. Quote an EXACT "
        "candidate substring showing that meaning; a claim ID or vague reference is insufficient. A broad "
        "disclaimer cannot replace a specific exception or condition. Shared scope/basis can cover several "
        "units if its application is unambiguous. For missing units use an empty quote. Counter-context need "
        "not reproduce rejected assistant words: check that the associated claim retains the limiting "
        "distinction without treating assistant statements as user endorsement. Separately list EVERY added "
        "unsupported preference or overgeneralization in unsupported, each with an exact quote and reason. "
        "Assess units independently of candidate self-claims. Never mark an omitted unit retained merely "
        "because the reference explains it. No imaginary scenarios or user answers.",
        {"reference": ref, "candidate": prompt})


def validate_audit(audit, ref, prompt):
    exact(audit, ("units", "unsupported"), "compression audit")
    if not isinstance(audit["units"], list) or not isinstance(audit["unsupported"], list):
        raise ValueError("Audit entries must be lists")
    ids = []
    for item in audit["units"]:
        exact(item, ("unit_id", "verdict", "quote", "reason"), "unit audit")
        ids.append(string(item["unit_id"], "unit_id", 96))
        if item["verdict"] not in ("retained", "partial", "missing", "contradicted"):
            raise ValueError("Unsupported unit verdict")
        string(item["reason"], "audit reason", 16000)
        if item["verdict"] == "missing":
            if item["quote"] != "":
                raise ValueError("Missing units must have an empty quote")
        else:
            quote = string(item["quote"], "audit quote", 1000000)
            if quote not in prompt:
                raise ValueError("Audit quote does not occur in the candidate prompt")
    if len(ids) != len(set(ids)) or set(ids) != {u["id"] for u in ref["units"]}:
        raise ValueError("Audit must cover every reference unit exactly once")
    for item in audit["unsupported"]:
        exact(item, ("quote", "reason"), "unsupported addition")
        if string(item["quote"], "unsupported quote", 1000000) not in prompt:
            raise ValueError("Unsupported addition quote is absent from the candidate")
        string(item["reason"], "unsupported reason", 16000)
    return audit


def metrics(ref, audit, prompt, budget, detailed_length):
    verdicts = {u["unit_id"]: u["verdict"] for u in audit["units"]}
    retained = {uid for uid, verdict in verdicts.items() if verdict == "retained"}
    claim_ids = set(u["claim_id"] for u in ref["units"] if u["claim_id"] is not None)
    complete = [cid for cid in sorted(claim_ids) if all(u["id"] in retained for u in ref["units"] if u["claim_id"] == cid)]
    critical = [u for u in ref["units"] if u["kind"] in ("condition", "exception", "counter_context", "unknown")]
    return {"prompt_characters": len(prompt), "prompt_bytes": len(prompt.encode()), "tokens": None,
            "character_ratio_to_detailed": len(prompt) / detailed_length,
            "model_judged_retained_units": len(retained), "reference_units": len(ref["units"]),
            "model_judged_complete_claims": len(complete), "reference_claims": len(claim_ids),
            "critical_units": len(critical), "model_judged_retained_critical_units": sum(u["id"] in retained for u in critical),
            "unsupported_additions": len(audit["unsupported"]), "within_budget": len(prompt) <= budget,
            "accepted": len(prompt) <= budget and len(retained) == len(ref["units"]) and not audit["unsupported"],
            "failed_unit_ids": [u["id"] for u in ref["units"] if u["id"] not in retained]}


def audit_prompt(profile, prompt, destination, review_model, budget=1000, resume=False,
                 generate=codex_generate, progress=lambda message: None):
    string(prompt, "candidate prompt", 128000)
    ref = reference(profile)
    detailed, _ = export_profile(profile)
    configuration = {**compression_plan(profile, budget, 1), "operation": "audit_only",
                     "model": review_model, "candidate_sha256": digest(prompt), "model_calls_upper_bound": 1}
    journal = Journal(destination, configuration, resume, generate, progress)
    lock = journal.path / ".build.lock"
    try:
        fd = os.open(str(lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise ValueError("Audit run is locked; verify its process stopped before removing .build.lock")
    try:
        os.close(fd)
        audit = journal.call("audit", audit_request(ref, prompt), AUDIT_SCHEMA)
        validate_audit(audit, ref, prompt)
        summary = {"status": "model_audit_complete", "profile_id": profile["id"],
                   "candidate_sha256": digest(prompt), "review_model": review_model,
                   **metrics(ref, audit, prompt, budget, len(detailed)), "independent_fidelity_verified": False,
                   "note": "Quote-anchored model comparison to the reference profile; not a behavior or RIG score."}
        write_once(journal.path / "reference.private.json", ref)
        write_once(journal.path / "candidate.private.md", prompt)
        write_once(journal.path / "summary.private.json", summary)
        return summary
    finally:
        lock.unlink()


def compress(profile, destination, model, review_model, budget=1000, attempts=2,
             resume=False, generate=codex_generate, progress=lambda message: None):
    configuration = {**compression_plan(profile, budget, attempts), "model": model, "review_model": review_model}
    if not model or not review_model:
        raise ValueError("Choose explicit generator and review models")
    journal = Journal(destination, configuration, resume, generate, progress)
    lock = journal.path / ".build.lock"
    try:
        fd = os.open(str(lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise ValueError("Compression run is locked; verify its process stopped before removing .build.lock")
    try:
        os.close(fd)
        return _compress(profile, journal, review_model, budget, attempts)
    finally:
        lock.unlink()


def _compress(profile, journal, review_model, budget, attempts):
    ref = reference(profile)
    detailed, detailed_manifest = export_profile(profile)
    write_once(journal.path / "reference.private.json", ref)
    write_once(journal.path / "detailed.private.md", detailed)
    write_once(journal.path / "detailed-export.private.json", detailed_manifest)
    write_once(journal.path / "detailed.portable.json", make_expression(detailed, profile["id"], "detailed"))
    previous, feedback, rows, winner = None, None, [], None
    for index in range(attempts):
        proposal = journal.call(f"attempt-{index}-generate", generation_request(ref, budget, previous, feedback), TEXT_SCHEMA)
        exact(proposal, ("text",), "compression proposal")
        body = string(proposal["text"], "compressed text", 1000000)
        prompt = HEADER + body.strip() + "\n"
        write_once(journal.path / f"attempt-{index}.private.md", prompt)
        if len(prompt) > budget:
            row = {"attempt": index, "prompt_characters": len(prompt), "accepted": False,
                   "reason": "over_budget", "audit_performed": False}
            feedback = {"problem": "Candidate exceeds the complete character budget", "characters": len(prompt), "budget": budget}
        else:
            audit = journal.call(f"attempt-{index}-audit", audit_request(ref, prompt), AUDIT_SCHEMA, model=review_model)
            validate_audit(audit, ref, prompt)
            row = {"attempt": index, "audit_performed": True, **metrics(ref, audit, prompt, budget, len(detailed))}
            feedback = audit
            if row["accepted"]:
                winner = prompt
        rows.append(row)
        write_once(journal.path / f"attempt-{index}.metrics.private.json", row)
        if winner is not None:
            break
        previous = prompt
    summary = {"status": "model_audited_candidate" if winner else "no_faithful_candidate_within_budget",
               "profile_id": profile["id"], "budget_characters": budget, "detailed_characters": len(detailed),
               "generator_model": journal.model, "review_model": review_model,
               "same_model_review": journal.model == review_model, "attempts": rows,
               "prompt_available": winner is not None, "independent_fidelity_verified": False,
               "note": "Quote existence is checked mechanically; preservation verdicts remain fallible model judgments. No RIG or behavior reproduction claim."}
    if winner is not None:
        write_once(journal.path / "prompt.md", winner)
        write_once(journal.path / "portable.json", make_expression(winner, profile["id"], "facet_audited_compression_v1"))
    write_once(journal.path / "summary.private.json", summary)
    return summary
