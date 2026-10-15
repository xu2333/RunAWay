"""Portable public expression, with evidence kept in a separate private record."""
import hashlib
import json

BOUNDARY = ("Use this as a tentative preference for relevant choices, subject to the current task "
            "and explicit user instructions. It is not a factual identity or permission to act.")
KINDS = ("experience", "resume", "trajectory")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def string(value, field, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{field} must be nonempty text of at most {limit} characters")
    if any(ord(c) < 32 and c not in "\n\t\r" for c in value):
        raise ValueError(f"Control characters in {field}")
    if "<!-- runaway:" in value.lower() or "<|im_" in value:
        raise ValueError(f"Reserved delimiters in {field}")
    return value


def make_card(answer, source, kind, provenance):
    if kind not in KINDS:
        raise ValueError("Unknown input kind")
    required = {"name", "tagline", "prompt", "limits", "evidence"}
    if not isinstance(answer, dict) or set(answer) != required:
        raise ValueError("Expected exactly: name, tagline, prompt, limits, evidence")
    public = {k: string(answer[k], k, limit) for k, limit in
              [("name", 40), ("tagline", 160), ("prompt", 1200)]}
    limits = answer["limits"]
    if not isinstance(limits, list) or not 1 <= len(limits) <= 5:
        raise ValueError("Provide 1–5 limitations")
    public["limits"] = [string(x, "limit", 240) for x in limits]
    evidence = answer["evidence"]
    if not isinstance(evidence, list) or not 1 <= len(evidence) <= 8:
        raise ValueError("Provide 1–8 evidence anchors")
    for entry in evidence:
        if not isinstance(entry, dict) or set(entry) != {"claim", "quote", "scope"}:
            raise ValueError("Evidence needs claim, quote, scope")
        for key, maximum in [("claim", 300), ("quote", 400), ("scope", 300)]:
            string(entry[key], key, maximum)
        if entry["quote"] not in source:
            raise ValueError("Evidence quote is not an exact substring of the input")
    card = {"schema_version": 1, "status": "candidate_unvalidated", **public}
    card["id"] = digest(canonical(card))[:16]
    private = {"source_sha256": digest(source), "source_kind": kind,
               "card_id": card["id"], "evidence": evidence, "provenance": provenance,
               "validation": "Quote existence checked; semantic support and privacy not guaranteed."}
    return card, private


def validate_card(card):
    expected = {"schema_version", "status", "name", "tagline", "prompt", "limits", "id"}
    if not isinstance(card, dict) or set(card) != expected or card["schema_version"] != 1:
        raise ValueError("Unsupported card schema")
    if card["status"] != "candidate_unvalidated":
        raise ValueError("Unsupported validation status")
    for key, limit in [("name", 40), ("tagline", 160), ("prompt", 1200)]:
        string(card[key], key, limit)
    if not isinstance(card["limits"], list) or not 1 <= len(card["limits"]) <= 5:
        raise ValueError("Invalid limitations")
    for value in card["limits"]:
        string(value, "limit", 240)
    if card["id"] != digest(canonical({k: v for k, v in card.items() if k != "id"}))[:16]:
        raise ValueError("Card changed: re-import the edited answer to create its new identity")
    return card


def render(card):
    validate_card(card)
    return (f"# RunAWay · {card['name']}\n\n{card['tagline']}\n\n"
            f"{card['prompt']}\n\nScope / uncertainty: {' '.join(card['limits'])}\n\n"
            + BOUNDARY + "\n")


def parse_answer(text):
    text = text.strip()
    if text.startswith("```json\n") and text.endswith("```"):
        text = text[8:-3].strip()
    return json.loads(text)
