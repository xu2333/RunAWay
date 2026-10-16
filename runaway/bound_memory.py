"""Concise prose with program-bound private facets, not model-rewritten quotes."""
from pathlib import Path
from .card import string
from .compression import HEADER, reference
from .decision_memory import projected
from .profile import exact, object_schema, STR, STRINGS
from .review import request
from .pipeline import write_once
from .portable import make_expression

SCHEMA=object_schema({'scope':STR,'clauses':{'type':'array','items':object_schema({'claim_ids':STRINGS,'text':STR})},'unknown':STR})


def make_request(profile,budget):
    if type(budget) is not int or not 200<=budget<=16000:raise ValueError('Invalid Unicode character budget')
    return request(
        'Compress the supplied evidence-linked profile into compact natural prose in its language. '
        'Use concrete condition→action wording without numbering or personality axes. '
        'This is a context-bound candidate memory, not a universal identity or permission to act. '
        'No hidden policies or test cases are supplied. Do not infer new preferences. '
        'Keep all chosen actions, ordinary conditions, exceptions, repeated-versus-single observations, reversibility, '
        'numeric conditions, historical scope and unknown thresholds. Explicitly state what action is RETAINED '
        'when a condition changes; epistemic negation alone is not a choice. Preserve atypical preferences. '
        'Put shared scope/basis/uncertainty once in scope, not repeated in every clause. '
        'Each claim has exactly one clause with its original claim_id. Related claims must both stay present. '
        'Clauses contain text and claim_ids only. Do not retype source anchors: code attaches the original profile facets privately. '
        'Use the supplied fixed header exactly via the renderer; do not repeat it. Current user instructions override history. '
        'Use succinct wording, semicolons and numbers where useful; no ornamental introduction or invented biography. '
        'Return scope, clauses, unknown. Scope and unknown are short prose. All strings must contain intact Unicode. '
        f'The full rendered memory HEADER+scope+joined clause texts+unknown is at most {budget} Unicode characters, including header. '
        'All facets still need to be recoverable. Budget private claim IDs as zero, since they are not rendered.',
        {'reference':projected(profile),'fixed_header':HEADER,'budget_characters':budget,
         'render_format':'HEADER + scope + newline + clauses joined with ； + newline + unknown'})


def render(value):
    return HEADER+value['scope'].strip()+'\n'+'；'.join(c['text'].strip().rstrip('；。') for c in value['clauses'])+'。\n'+value['unknown'].strip()


def bind(value,profile,budget):
    ref=projected(profile);exact(value,('scope','clauses','unknown'),'bound memory')
    string(value['scope'],'scope',1000);string(value['unknown'],'unknown',1000)
    if not isinstance(value['clauses'],list) or len(value['clauses'])!=len(ref['claims']):raise ValueError('Exactly one clause for each claim is required')
    ids={c['id'] for c in ref['claims']};covered=set();bindings=[]
    facets=reference(profile)['units']
    for i,clause in enumerate(value['clauses']):
        exact(clause,('claim_ids','text'),'bound clause');string(clause['text'],'clause text',16000)
        linked=clause['claim_ids']
        if not isinstance(linked,list) or len(linked)!=1 or not isinstance(linked[0],str) or linked[0] not in ids or linked[0] in covered:raise ValueError('Unknown, missing or repeated claim reference')
        covered.add(linked[0])
        bindings.append({'clause_index':i,'claim_id':linked[0],
                         'original_facets':[u for u in facets if u['claim_id']==linked[0]]})
    if covered!=ids:raise ValueError('Missing claims')
    text=render(value)
    if len(text)>budget:raise ValueError(f'Bound memory exceeds budget: {len(text)} > {budget}; no truncation')
    return text,{'bindings':bindings,'unknown_facets':[u for u in facets if u['claim_id'] is None],
                 'interpretation':'Program copies original profile facets; binding checks identity only, not semantic preservation of clause text.'}


def import_candidate(value,profile,destination,budget=1000):
    text,bindings=bind(value,profile,budget)
    expression=make_expression(text,profile['id'],'program_bound_manual_unverified_v3')
    out=Path(destination);out.mkdir(parents=True,exist_ok=False)
    write_once(out/'candidate.private.json',value);write_once(out/'bindings.private.json',bindings)
    write_once(out/'portable.json',expression);write_once(out/'prompt.md',text)
    summary={'status':'candidate_unvalidated','characters':len(text),'profile_id':profile['id'],'portable_id':expression['id'],
             'model_calls':0,'source_binding_checked':True,'semantic_preservation_verified':False,'behavioral_fidelity_verified':False,
             'warning':'Manual candidate only. Private facet binding is not a semantic audit or a promotion. Current instructions take precedence.'}
    write_once(out/'summary.private.json',summary);return summary
