"""Audit paired observations and recount registered outcomes offline."""
from collections import Counter
from pathlib import Path
import hashlib
import json


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def tally(root):
    protocol = load(root / "protocol.json")
    cases = {c["id"]: c for c in protocol["cases"]}
    clients = protocol["clients"]
    baseline = load(root.parent / "historical-cross-harness-v1" / "protocol.json")
    assert protocol["cases"] == baseline["cases"] and clients == baseline["clients"]
    historical = load(root.parent / "historical-cross-harness-v1" / "observations.json")
    historical_passes = {r["client"] + "/" + r["case"] for r in historical if r["content_pass"]}
    assert historical_passes == set(protocol["historical_pass_watch"])
    records = load(root / "observations.json")
    rows = {(r["client"], r["case"], r["arm"]): r for r in records}
    keys = {(client, case, arm) for client in clients for case in cases for arm in ("old","new")}
    assert set(rows) == keys and len(rows) == len(records) == protocol["max_cli_attempts"]
    assert {r["slot"] for r in records} == {r["slot"] for r in protocol["slots"]}
    for row in rows.values():
        assert row["slot"] == "-".join((row["client"], row["case"], row["arm"]))
        if row.get("missing"):
            assert "answer" not in row and row["strict_pass"] is False
            continue
        raw = row["answer"]
        assert row["next_action_usable"] in ("yes", "partial", "no")
        assert hashlib.sha256(raw.encode()).hexdigest() == row["answer_sha256"]
        clauses = row["clauses"]
        assert len(clauses) == len(cases[row["case"]]["assess_separately"])
        for clause in clauses:
            assert clause["mark"] in ("pass","partial_or_omitted","contradicted")
            assert clause["quotes"] and all(q and q in raw for q in clause["quotes"])
        genuine = row["genuine_prerequisites"]
        assert genuine["status"] in ("intact","weakened","removed")
        for issue in (genuine, row["extra_gate"], row["forced_immediacy"], row["other_material_conflict"]):
            if issue is not None:
                assert issue["evidence"] and all(q and q in raw for q in issue["evidence"])
        assert row["strict_pass"] == (all(c["mark"] == "pass" for c in clauses)
            and genuine["status"] == "intact" and not any(row[k] for k in ("extra_gate","forced_immediacy","other_material_conflict")))
    result = {}
    for arm in ("old","new"):
        group = [r for r in rows.values() if r["arm"] == arm]
        present = [r for r in group if not r.get("missing")]
        result[arm] = dict(
            denominator=len(group), missing=len(group)-len(present),
            strict={client:sum(r["strict_pass"] for r in group if r["client"] == client) for client in clients},
            all_three=[c for c in cases if all(rows[client,c,arm]["strict_pass"] for client in clients)],
            extra_gate=sum(bool(r["extra_gate"]) for r in present),
            genuine=dict(Counter(r["genuine_prerequisites"]["status"] for r in present)),
            forced=sum(bool(r["forced_immediacy"]) for r in present))
    transitions = {}
    for field in ("extra_gate","strict_pass","genuine_loss","forced_immediacy"):
        counts = Counter()
        for client in clients:
            for case in cases:
                pair = [rows[client,case,a] for a in ("old","new")]
                if any(r.get("missing") for r in pair):
                    counts["missing"] += 1
                    continue
                states = [r["genuine_prerequisites"]["status"] != "intact" if field == "genuine_loss" else bool(r[field]) for r in pair]
                counts[" -> ".join(str(x) for x in states)] += 1
        transitions[field] = dict(counts)
    result["paired"] = transitions
    result["historical_pass_watch"] = {key:[rows[(*key.split("/"),a)]["strict_pass"] for a in ("old","new")] for key in protocol["historical_pass_watch"]}
    return result

if __name__ == "__main__":
    print(json.dumps(tally(Path(__file__).resolve().parent), indent=2))
