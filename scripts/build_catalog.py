"""Compile the explicitly authored fictional catalogue; never read user histories."""
import argparse
import hashlib
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ["01-04.txt", "05-08.txt", "09-12.txt", "13-16.txt", "17-20.txt", "21-24.txt", "25-28.txt"]
OUTPUT = ROOT / "web/dist/catalog.json"


def normalize(text):
    return "".join(c.lower() for c in unicodedata.normalize("NFKC", text)
                   if unicodedata.category(c)[0] not in "PZS" and not c.isspace())


def compile_catalog(root=ROOT):
    categories, entries, digest = [], [], hashlib.sha256()
    current = None
    seen = {key: set() for key in ("name", "tagline", "tell")}
    for filename in SOURCES:
        raw = (root / "catalog" / filename).read_bytes()
        digest.update(filename.encode() + b"\0" + raw)
        for line_no, line in enumerate(raw.decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            fields = [field.strip() for field in line.split("|")]
            if line.startswith("@"):
                if len(fields) != 3 or not all(fields):
                    raise ValueError("Invalid category header")
                current = {"id": fields[0][1:], "name": fields[1], "boundary": fields[2]}
                if any(c["id"] == current["id"] for c in categories):
                    raise ValueError("Duplicate category")
                categories.append(current)
                continue
            if current is None or len(fields) != 3:
                raise ValueError(f"Invalid entry: {filename}:{line_no}")
            card = dict(zip(("name", "tagline", "tell"), fields))
            card["boundary"] = current["boundary"]
            for key, limit in (("name", 40), ("tagline", 160), ("tell", 100), ("boundary", 100)):
                value = card[key]
                if not value or len(value) > limit or any(ord(c) < 32 for c in value):
                    raise ValueError(f"Invalid {key}: {filename}:{line_no}")
                if key in seen:
                    normalized = normalize(value)
                    if normalized in seen[key]:
                        raise ValueError(f"Duplicate {key}: {value}")
                    seen[key].add(normalized)
            entries.append({"id": f"RW-{len(entries) + 1:04d}", "category": current["id"],
                            "origin": "synthetic_catalog", "card": card})
    counts = {c["id"]: sum(e["category"] == c["id"] for e in entries) for c in categories}
    if len(entries) != 700 or len(categories) != 28 or set(counts.values()) != {25}:
        raise ValueError(f"Expected 28 x 25 = 700 authored entries; got {counts}")
    return {"schema_version": 1, "artifact_type": "runaway_synthetic_catalog", "catalog_version": "1.0.0",
            "provenance": "AI-authored original fiction; no user submissions or private trajectories used.",
            "source_sha256": digest.hexdigest(), "categories": categories, "entries": entries}


def audit(catalog):
    pairs = []
    entries = catalog["entries"]
    for field, threshold in (("name", .55), ("tagline", .65), ("tell", .65)):
        grams = []
        for entry in entries:
            value = normalize(entry["card"][field])
            grams.append(set(zip(value, value[1:])))
        for i, left in enumerate(grams):
            for j in range(i + 1, len(grams)):
                right = grams[j]
                score = len(left & right) / max(1, len(left | right))
                if score >= threshold:
                    pairs.append({"field": field, "ids": [entries[i]["id"], entries[j]["id"]],
                                  "text": [entries[i]["card"][field], entries[j]["card"][field]],
                                  "similarity": round(score, 3)})
    return {"authored_entries": len(entries), "categories": len(catalog["categories"]),
            "exact_duplicates": 0, "near_duplicate_review": pairs,
            "note": "Count and textual uniqueness only. Overlapping behaviors are intentional; humor, fidelity and sharing need separate evaluation. Category boundaries are shared editorial cautions, not inferred traits."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if committed browser data differs from source")
    args = parser.parse_args()
    catalog = compile_catalog()
    encoded = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != encoded:
            raise SystemExit("catalog.json is stale; run python3 scripts/build_catalog.py")
    else:
        OUTPUT.write_text(encoded, encoding="utf-8")
    print(json.dumps(audit(catalog), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
