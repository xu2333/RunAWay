"""Reversible display boundaries for existing condition/action pairs."""
_ESCAPE={'\\':'\\\\','\n':'\\n','\r':'\\r','「':'\\「','」':'\\」','→':'\\→'}
_UNESCAPE={encoded[1:]:char for char,encoded in _ESCAPE.items()}


def _escape(text):
    return ''.join(_ESCAPE.get(char,char) for char in text)


def _unescape(text):
    result=[];index=0
    while index<len(text):
        char=text[index];index+=1
        if char=='\\':
            if index==len(text) or text[index] not in _UNESCAPE:raise ValueError('Invalid scope-row escape')
            char=_UNESCAPE[text[index]];index+=1
        result.append(char)
    return ''.join(result)


def parse_pairs(body):
    if not body:return []
    pairs=[]
    for line in body.split('\n'):
        if not line.startswith('「'):raise ValueError('Missing scope-row opening')
        index=1
        while index<len(line):
            if line[index]=='\\':index+=2;continue
            if line[index:index+2]=='」→':break
            index+=1
        if line[index:index+2]!='」→':raise ValueError('Missing scope/action separator')
        pairs.append((_unescape(line[1:index]),_unescape(line[index+2:])))
    return pairs


def render_pairs(pairs):
    pairs=list(pairs)
    if any(type(field) is not str for pair in pairs for field in pair):raise ValueError('Scope-row fields must be strings')
    body='\n'.join('「'+_escape(condition)+'」→'+_escape(action) for condition,action in pairs)
    if parse_pairs(body)!=pairs:raise ValueError('Scope-row round trip differs')
    return body
