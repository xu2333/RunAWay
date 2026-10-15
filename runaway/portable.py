"""A full prompt transport artifact, independent of the legacy card length limit."""
from .card import canonical, digest, render as render_card, string, validate_card
from .profile import exact


def make_expression(text, profile_id, method):
    string(text, "portable text", 1000000)
    value = {"schema_version": 1, "artifact_type": "portable_expression", "status": "candidate_unvalidated",
             "text": text, "profile_id": profile_id, "method": method}
    value["id"] = digest(canonical(value))
    return value


def validate_expression(value):
    if isinstance(value, dict) and value.get("artifact_type") == "portable_expression":
        exact(value, ("schema_version", "artifact_type", "status", "text", "profile_id", "method", "id"), "expression")
        if type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["status"] != "candidate_unvalidated":
            raise ValueError("Unsupported expression format")
        for key in ("text", "profile_id", "method"):
            string(value[key], key, 1000000 if key == "text" else 200)
        if value["id"] != digest(canonical({k: v for k, v in value.items() if k != "id"})):
            raise ValueError("Portable expression changed; export it again")
        return value
    return validate_card(value)


def render_expression(value):
    validate_expression(value)
    return value["text"] if value.get("artifact_type") == "portable_expression" else render_card(value)
