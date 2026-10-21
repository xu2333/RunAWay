"""A portable task contract for identifiable choices, not a preference oracle."""
from .card import canonical

IDENTIFIABLE = (
    '根据材料还原截至2026-04-01可确定的个人选择，不是推荐更明智的方案。'
    'A/B是本题两个选项；U是本题条件下无法从记录确定选择，所有题均可用U。'
    'U不等于这个领域从未谈过：即使同领域有偏好，关键条件超出观察范围且无适用规则时，也应U。'
    '新题材或措辞变化本身不是未知；条件相同则迁移已有选择，例外优先，同条件的明确新决定覆盖旧决定。'
    '题目省略细节时，区分信息不足和角色本人面对不确定风险：本题问记录能确定什么。'
    '若所有可能适用的已记录分支都选同一项，仍选该项；若分支选择不同且缺少区分信息，选U。'
    '不要只因缺一项细节就弃权，也不要用常识、保守建议或另一个条件的偏好补成本题的选择。'
    '没有同条件改口，不把历史决定仅因未重测而撤销；助手建议不是用户背书。'
    '每题独立，你在其他题的答案不是新证据。只返回题号到A/B/U的完整JSON。')


def make_request(material, queries):
    """No gold, domain names or case types appear in the protocol."""
    if type(material) is not str or not isinstance(queries, list) or not queries:
        raise ValueError('Provide text material and nonempty queries')
    ids = set()
    for q in queries:
        if type(q) is not dict or set(q) != {'id', 'scenario', 'options'}:
            raise ValueError('Queries require exactly id, scenario and options')
        if type(q['id']) is not str or not q['id'] or q['id'] in ids:
            raise ValueError('Query IDs must be nonempty and unique')
        if type(q['scenario']) is not str or not q['scenario'].strip() or type(q['options']) is not dict or set(q['options']) != {'A', 'B'}:
            raise ValueError('Invalid scenario/options')
        if any(type(v) is not str or not v.strip() for v in q['options'].values()):
            raise ValueError('Options must be nonempty text')
        ids.add(q['id'])
    schema = {'type':'object','additionalProperties':False,'required':[q['id'] for q in queries],
              'properties':{q['id']:{'type':'string','enum':['A','B','U']} for q in queries}}
    return {'schema':schema, 'prompt':IDENTIFIABLE+'\nANSWER_SCHEMA_JSON:\n'+canonical(schema)
            +'\nREADER_INPUT_JSON:\n'+canonical({'material':material,'queries':queries})}
