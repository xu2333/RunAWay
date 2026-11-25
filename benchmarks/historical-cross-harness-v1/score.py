"""Recompute matched counts from reported qualitative judgments, without inference."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))

def summarize():
    protocol = load("protocol.json")
    cases = {item["id"]: item for item in protocol["cases"]}
    clients = list(protocol["clients"])
    observed = {}
    for row in load("observations.json"):
        case_id, client = row["case"], row["client"]
        key = (case_id, client)
        assert key not in observed and case_id in cases and client in clients
        observed[key] = row
        if row.get("missing"):
            assert row["content_pass"] is False and "answer" not in row
            continue
        answer = row["answer"]
        assert hashlib.sha256(answer.encode("utf-8")).hexdigest() == row["answer_sha256"]
        clauses = row["clauses"]
        assert len(clauses) == len(cases[case_id]["assess_separately"])
        for item in clauses:
            assert item["mark"] in ("pass", "partial_or_omitted", "contradicted")
            assert item["quote"] and item["quote"] in answer
        assert row["content_pass"] == (all(item["mark"] == "pass" for item in clauses) and not row["material_conflict"])
    assert set(observed) == {(case, client) for case in cases for client in clients}
    counts = {client: sum(observed[case, client]["content_pass"] for case in cases) for client in clients}
    common = [case for case in cases if all(observed[case, client]["content_pass"] for client in clients)]
    clause_passes = {client: sum(part["mark"] == "pass" for case in cases for part in observed[case, client].get("clauses", [])) for client in clients}
    return {"registered_clauses_per_client": sum(len(c["assess_separately"]) for c in cases.values()), "clause_passes": clause_passes, "cases": len(cases), "cells": len(observed), "missing": sum(bool(row.get("missing")) for row in observed.values()), "per_client": counts, "all_three": common}

if __name__ == "__main__":
    print(json.dumps(summarize(), indent=2))
