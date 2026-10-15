"""Offline tour using a packaged, explicitly fictional completed example."""
import json
from importlib.resources import files

from .card import digest
from .pipeline import report_html
from .portable import make_expression, validate_expression
from .profile import export_profile, validate_profile


def demo_bundle():
    data = json.loads(files("runaway").joinpath("assets/demo.json").read_text(encoding="utf-8"))
    candidate = validate_profile(data["candidate"])
    profile = validate_profile(data["profile"])
    portable = validate_expression(data["portable"])
    if portable["profile_id"] != profile["id"] or digest(portable["text"]) != data["compact_manifest"]["prompt_sha256"]:
        raise ValueError("Packaged demo integrity mismatch")
    detailed, manifest = export_profile(profile)
    review = data["review"]
    summary = {"status": "offline_fictional_demo", "personalized_to_you": False, "model_calls": 0,
               "candidate_claims": len(candidate["claims"]), "review_supported_claims": len(profile["claims"]),
               "possible_omissions": len(review["omissions"]), "prompt_characters": len(portable["text"]),
               "independent_fidelity_verified": False,
               "note": "Pre-generated fictional book-club example. Model verdicts belong to the saved example; nothing was inferred about you."}
    return {"candidate.private.json": candidate, "profile.private.json": profile,
            "sources.private.json": profile["sources"], "review.private.json": review,
            "prompt.md": portable["text"], "portable.json": portable,
            "detailed.private.md": detailed, "detailed-export.private.json": manifest,
            "detailed.portable.json": make_expression(detailed, profile["id"], "detailed"),
            "compact-export.private.json": data["compact_manifest"], "summary.private.json": summary,
            "review.private.html": report_html(candidate, review["reviews"], review["omissions"], summary, portable["text"])}, summary
