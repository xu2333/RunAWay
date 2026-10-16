"""Evidence-linked condition/action memory. Structural checks are not semantic proof."""
from pathlib import Path
from .card import canonical, digest, string, parse_answer
from .compression import HEADER,reference,audit_request,AUDIT_SCHEMA,validate_audit,metrics
from .generation import codex_generate
from .pipeline import write_once
from .portable import make_expression
from .profile import STR, STRINGS, exact, object_schema, validate_profile, export_profile
from .review import request

SCHEMA=object_schema({'scope':STR,'rules':{'type':'array','items':object_schema({
    'when':STR,'prefer':STR,'qualification':STR,'claim_ids':STRINGS,
    'anchors':{'type':'array','items':object_schema({'claim_id':STR,'quote':STR})}})},'unknown':STR})


def projected(profile):
    validate_profile(profile)
    if not profile['claims']:raise ValueError('No observed claims to compress into decision branches')
    return {'profile_id':profile['id'],'claims':[{k:c[k] for k in ('id','statement','basis','scope','conditions','exceptions','related_claim_ids')} for c in profile['claims']],
            'unknowns':profile['unknowns']}


def make_request(profile,budget=1000):
    ref=projected(profile)
    if type(budget) is not int or not 200<=budget<=16000:raise ValueError('budget must be 200–16000 Unicode characters')
    return request(
        'Compress only the supplied evidence-linked profile into readable condition/action branches in its language. '
        'No hypothetical test cases, hidden rules, choices or reference answers are supplied or should be invented. '
        'This is a candidate preference memory, not a command to act. Match the scope of the observations. '
        'Treat an explicitly observed choice as a choice: say what the person STILL chose when a condition changed. '
        'Do not replace a supported unchanged choice with only an epistemic negation such as "cannot infer that feedback changes the design". '
        'Preserve separately the action under the ordinary condition and the action under its exception. '
        'If a claim says the same action remained despite a changed condition, state the retained action positively. '
        'Do not replace unusual choices with conventional, safer or more agreeable choices. '
        'Keep the historical basis and scope, uncertainty, numeric conditions, exceptions and conflicts. '
        'Current user instructions override historical preference; no permission to act. '
        'Do not repeat the fixed header in any field. Share a concise scope/uncertainty sentence once; do not repeat broad disclaimers after each rule so that they drown out the choice. '
        'Do not turn a single observation into a universal trait. Unknown domains remain unknown. '
        'Return scope, rules, unknown. Each rule has when (condition), prefer (chosen action), qualification (bounds/exception; empty if none), '
        'claim_ids and anchors. Each anchor has claim_id and quote, copied EXACTLY from that claim statement/scope/conditions/exceptions. '
        'Give EACH supplied claim its own separate rule with exactly one claim_id and an exact anchor. Do not merge opposed or unchanged-condition branches. Linked rules must all remain in the complete memory. '
        'Do not print IDs, anchors, biography or source quotes in the rendered prose. Do not invent fixed personality axes or labels. '
        f'The complete rendered text is header + scope + rules + unknown, at most {budget} Unicode characters. '
        'Budget these rendered strings only; anchors stay private. Use concrete compact wording, not a numbered personality list.',
        {'reference':ref,'fixed_header':HEADER,'render_format':'HEADER + scope + newline + each (when + ， + prefer + 。 + qualification) + newline + unknown','budget':budget})


def render(value):
    rules=[''.join([r['when'].rstrip('，。;；'), '，',r['prefer'].rstrip('。;；'),'。',r['qualification']]) for r in value['rules']]
    return HEADER+value['scope'].replace(HEADER.strip(),'').strip()+'\n'+''.join(rules)+'\n'+value['unknown'].strip()+'\n'


def validate(value,profile,budget=1000):
    ref=projected(profile);exact(value,('scope','rules','unknown'),'decision memory')
    string(value['scope'],'scope',400);string(value['unknown'],'unknown',600)
    if not isinstance(value['rules'],list) or not 1<=len(value['rules'])<=30:raise ValueError('Provide 1–30 decision branches')
    claims={c['id']:c for c in ref['claims']};covered=set()
    for rule in value['rules']:
        exact(rule,('when','prefer','qualification','claim_ids','anchors'),'decision branch')
        string(rule['when'],'when',300);string(rule['prefer'],'prefer',300)
        if not isinstance(rule['qualification'],str) or len(rule['qualification'])>400:raise ValueError('Invalid qualification')
        if rule['qualification']:string(rule['qualification'],'qualification',400)
        ids=rule['claim_ids']
        if not isinstance(ids,list) or len(ids)!=1 or len(ids)!=len(set(ids)) or any(i not in claims for i in ids):raise ValueError('Unknown or duplicate claim reference')
        if not isinstance(rule['anchors'],list):raise ValueError('anchors must be a list')
        anchored=set()
        for a in rule['anchors']:
            exact(a,('claim_id','quote'),'anchor');cid=a['claim_id']
            if cid not in ids:raise ValueError('Anchor must refer to a claim in this branch')
            quote=string(a['quote'],'quote',16000);c=claims[cid]
            corpus=[c['statement'],c['scope'],*c['conditions'],*c['exceptions']]
            if not any(quote in text for text in corpus):raise ValueError('Anchor is not an exact profile substring')
            anchored.add(cid)
        if anchored!=set(ids):raise ValueError('Every referenced claim needs a private exact anchor')
        if set(ids)&covered:raise ValueError('Each claim must have exactly one dedicated branch')
        covered.update(ids)
    if covered!=set(claims):raise ValueError('All claims must be covered; no silent omission')
    text=render(value)
    if len(text)>budget:raise ValueError(f'Decision memory exceeds budget: {len(text)} > {budget}; no truncation')
    return text


def semantic_audit(value,profile,budget,generate,model):
    text=validate(value,profile,budget);ref=reference(profile)
    raw,provenance=generate(audit_request(ref,text),model,schema=AUDIT_SCHEMA,system='Text-only semantic auditor. Return only the requested JSON.')
    audit=parse_answer(raw);validate_audit(audit,ref,text)
    detailed,_=export_profile(profile)
    result=metrics(ref,audit,text,budget,len(detailed))
    return audit,result,provenance

def compress(profile,destination,model,budget=1000,generate=codex_generate,review_model=None):
    if not model:raise ValueError('Choose an explicit model')
    prompt=make_request(profile,budget);out=Path(destination);out.mkdir(parents=True,exist_ok=False)
    write_once(out/'request.private.txt',prompt)
    raw,provenance=generate(prompt,model,schema=SCHEMA,system='Text-only evidence compressor. No tools or actions. Return the requested JSON.')
    value=parse_answer(raw);write_once(out/'candidate.private.json',value)
    try:text=validate(value,profile,budget)
    except ValueError as exc:
        write_once(out/'failure.private.json',{'error':str(exc),'provenance':provenance});raise
    audit,result,audit_provenance=semantic_audit(value,profile,budget,generate,review_model or model)
    write_once(out/'audit.private.json',{'audit':audit,'metrics':result,'provenance':audit_provenance})
    if not result['accepted']:raise ValueError('Semantic audit rejected candidate; no portable expression exported')
    expression=make_expression(text,profile['id'],'condition_action_model_audited_v2')
    write_once(out/'portable.json',expression);write_once(out/'prompt.md',text)
    summary={'status':'candidate_unvalidated','profile_id':profile['id'],'portable_id':expression['id'],
             'characters':len(text),'tokens':None,'budget_characters':budget,'model_calls':2,'provenance':provenance,
             'model_judged_preservation':result,'claim_references_and_anchors_checked':True,'semantic_preservation_verified':False,'behavioral_fidelity_verified':False}
    write_once(out/'summary.private.json',summary);return summary
