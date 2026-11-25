"""Verify quoted evidence and recount fixed, paired denominators offline."""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

# Each field is scored from its own quoted passage, including conflicting summaries.
FIELDS = {
    "listening": {"material": {"faithful","narrow","ambiguous","omitted"}, "release": {"pass","fail"}},
    "foldout": {"timing": {"permission","immediate","blocked","ambiguous"}, "progress": {"pass","fail"},
                "photo": {"pass","fail"}, "release": {"pass","fail"}},
    "swatch": {"strip": {"pass","fail"}, "release": {"pass","fail"}},
    "thread": {"scope": {"pass","fail"}},
    "type": {"storage_counts_signatures": {"pass","fail"}},
}
ISSUES = {"added_gate","lost_gate","immediate","invented_state","conflict","omission","extra_work","no_handoff"}

def aggregate(directory=HERE):
    plan=load(directory/"protocol.json")
    rows=load(directory/"observations.json")
    cases={c["id"]:c for c in plan["cases"]}
    assert len(rows)==len(plan["slots"])==54
    assert len({r["slot"] for r in rows})==54
    closed=set()
    for cell,r in zip(plan["slots"],rows):
        assert all(r[k]==v for k,v in cell.items())
        if r.get("missing"):
            kind="not attempted after client failure" if r["client"] in closed else "client failure"
            assert r["missing"]==kind and not r["strict_pass"] and "answer" not in r
            closed.add(r["client"])
            continue
        assert r["client"] not in closed
        answer=r["answer"]
        assert hashlib.sha256(answer.encode()).hexdigest()==r["answer_sha256"]
        assert (r["answer_sha256"]!=r["original_answer_sha256"])==r["local_project_redacted"]
        assert len(r["clauses"])==len(cases[r["case"]]["assess_separately"])
        assert set(r["issues"])<=ISSUES and r["review"]
        assert all(c["mark"] in {"P","O","X"} for c in r["clauses"])
        for item in [*r["clauses"],*r["facets"].values()]:
            assert item["quotes"] and all(q and q in answer for q in item["quotes"])
        expected=FIELDS.get(r["case"],{})
        assert set(r["facets"])==set(expected)
        assert all(v["value"] in expected[k] for k,v in r["facets"].items())
        assert r["strict_pass"]==(all(c["mark"]=="P" for c in r["clauses"]) and not r["issues"])
    at={(r["arm"],r["client"],r["case"]):r for r in rows}
    clients=list(plan["clients"])
    previous=load(directory.parent/"object-action-waits-cross-harness-v1"/"observations.json")
    prior={(r["client"],r["case"]) for r in previous if r["arm"]=="new" and r["strict_pass"]}
    assert len(prior)==21
    report={}
    for arm in ("old","new"):
        per_client={}
        for cl in clients:
            def facet(case,field):
                return at[arm,cl,case].get("facets",{}).get(field,{}).get("value")
            material=facet("listening","material")
            release=facet("listening","release")=="pass"
            listening=release and material=="faithful"
            fold=facet("foldout","timing")=="permission" and facet("foldout","progress")=="pass" and facet("foldout","release")=="pass"
            per_client[cl]=dict(listening=listening,listening_lenient=release and material in {"faithful","ambiguous"},foldout=fold,joint=listening and fold,
                photo=facet("foldout","photo")=="pass" and facet("foldout","release")=="pass",
                strip=facet("swatch","strip")=="pass" and facet("swatch","release")=="pass",
                thread=facet("thread","scope")=="pass",specimen=facet("type","storage_counts_signatures")=="pass",
                strict=sum(at[arm,cl,c]["strict_pass"] for c in cases))
        group=[r for r in rows if r["arm"]==arm]
        report[arm]=dict(clients=per_client,all_three=[c for c in cases if all(at[arm,cl,c]["strict_pass"] for cl in clients)],
                         issues=dict(Counter(i for r in group for i in r.get("issues",[]))),missing=sum("missing" in r for r in group),
                         previous_21=sum(at[arm,cl,c]["strict_pass"] for cl,c in prior))
    changes=Counter()
    for cl in clients:
        for c in cases:
            pair=[at[a,cl,c] for a in ("old","new")]
            key="missing" if any("missing" in r for r in pair) else "→".join(str(int(r["strict_pass"])) for r in pair)
            changes[key]+=1
    report["pairs"]=dict(changes)
    return report

if __name__=="__main__":
    print(json.dumps(aggregate(),indent=2,ensure_ascii=False))
