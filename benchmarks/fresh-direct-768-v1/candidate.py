"""Source-only ID graph to a whole-budget public card; no inference transport.

Compose two existing reversible codecs. Selection is by character count only,
before seeing questions or answers. Private intermediate validation is not a
second public-memory allowance and never becomes reader input.
"""
import copy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


base = load('direct768_id_base', HERE.parent / 'source-id-initial-encoding-v1/candidate.py')
factor = load('direct768_common_factor', HERE.parent / 'common-condition-factor-v1/codec.py')
dense = factor.dense
VERSION = base.VERSION  # The source-ID graph wire and all witnesses are unchanged.
METHOD = 'direct_source_factor_v1'
INTERMEDIATE_CEILING = 16000  # Existing validator's maximum; never a delivered card.
GUIDANCE = '''本次最终公开卡必须满足GRAPH_INPUT_JSON的完整字符预算。以下只覆盖旧的公开渲染描述，不放宽任何来源、角色、别名、动作、改口或归属校验：
程序先完整校验同一份来源ID图，再在两种可逆公开写法中按字符数选择较短的合格结果：原dense写法；或把每一范围的每条规则都具有的完全相同且顺序相同的条件前缀，写成一行“每条规则另须本题所问项目满足=[完整条件字符串]”。该行只是各规则对本题项目的必要前提，不是事实或许可；其余条件、范围、动作、优先级、未知必须原样保留。仅部分分支需要的条件不能提到公共前提，也不能为了省字删掉。
两种写法均可用原有“先展开=”公开逐字词典；需要先按该卡内词典展开，再把公共前提分别加回每条规则。不向读卡器提供程序或私有图。词典、公共前提行、原guide、名字、标语和未知全部计入同一最终预算；超限就失败，不截断、不补图、不修卡。
内部完整校验不是额外公开预算。请从这份来源完整恢复选择和条件，精练自足标签；不要把提炼遗漏伪装成用户未知。最终字段格式仍为相同的来源ID图。'''


def make_request(sources, budget=768):
    request = base.make_request(sources, budget)
    request['prompt'] = GUIDANCE + '\n' + request['prompt']
    return request


def restore(text):
    return factor.restore(dense.decode(text))


def render(flat, budget=768):
    base.b.grouped.budget_check(budget)
    expanded = dense.decode(flat)
    expected = dense.parse(expanded)
    # This phase is syntax only: it has no source, question, reference or score.
    factored = factor.factor(expanded, max(len(expanded) * 2, 300))
    alternatives, errors = [], []
    for scheme, text in (('dense', expanded), ('common_then_dense', factored['prompt'])):
        try:
            prompt, dictionary = dense.pack(text, budget, prefix=dense.prefix(expected))
        except ValueError as exc:
            errors.append(dict(scheme=scheme, error=str(exc)))
            continue
        if restore(prompt) != expanded or dense.parse(restore(prompt)) != expected:
            raise ValueError('Composed public codecs changed an ordered field')
        alternatives.append((len(prompt), scheme != 'dense', scheme, prompt, dictionary))
    if not alternatives:
        raise ValueError('Neither complete reversible layout fits whole budget; no truncation')
    _, _, scheme, prompt, dictionary = min(alternatives)
    return dict(prompt=prompt, scheme=scheme, characters=len(prompt), budget_characters=budget,
                expanded_characters=len(expanded),
                common_conditions=factored['common_conditions'] if scheme != 'dense' else [],
                available_common_conditions=factored['common_conditions'],
                dictionary=dictionary, rejected_layouts=errors, ordered_projection_roundtrip_exact=True,
                character_selection_only=True, model_reader_fidelity_verified=False)


def bind(answer, sources, budget=768):
    base.b.grouped.budget_check(budget)
    files = base.bind(answer, sources, INTERMEDIATE_CEILING)
    rendered = render(files['prompt.md'], budget)
    intermediate = copy.deepcopy(files['profile.private.json'])
    profile = dict(schema_version=1, artifact_type='experimental_direct_source_factor_profile',
                   sources=copy.deepcopy(sources), graph=copy.deepcopy(answer),
                   budget_characters=budget, source_sha256=dense.digest(dense.canonical(sources)),
                   intermediate_profile_id=intermediate['id'],
                   public_projection=dense.grouped_projection(dense.parse(restore(rendered['prompt']))),
                   semantic_classification_verified=False, behavioral_fidelity_verified=False)
    profile['id'] = dense.digest(dense.canonical(profile))
    files['source-id-intermediate.private.json'] = intermediate
    files['profile.private.json'] = profile
    files['prompt.md'] = rendered['prompt']
    files['portable.json'] = dense.make_expression(rendered['prompt'], profile['id'], METHOD)
    files['encoding.private.json'] = rendered
    files['summary.private.json'].update(status='candidate_unvalidated', characters=rendered['characters'],
        budget_characters=budget, public_layout=rendered['scheme'],
        ordered_projection_roundtrip_exact=True, behavioral_fidelity_verified=False)
    return files
