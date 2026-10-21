"""Exact repeated-phrase dictionary packing. No model, truncation or paraphrase."""
import re
SYMBOLS='①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'
LABEL='词典（符号按原文展开）：'


def candidates(text):
    starts={0};ends={len(text)}
    for match in re.finditer(r'[，。；、\n]',text):
        starts.add(match.end());ends.add(match.start());ends.add(match.end())
    found=set()
    for start in sorted(starts):
        for end in sorted(ends):
            length=end-start
            if not 8<=length<=160:continue
            value=text[start:end]
            if value.strip('，。；、\n') and text.count(value)>=2 and not any(c in value for c in SYMBOLS):found.add(value)
    return found


def unpack(text,report):
    prefix=report['prefix'];dictionary=report['dictionary']
    if not dictionary:return text
    header=LABEL+'；'.join(key+'='+value for key,value in dictionary)+'。\n'
    if not text.startswith(prefix+header):raise ValueError('Encoded dictionary/prefix differs')
    body=text[len(prefix+header):]
    for key,value in dictionary:body=body.replace(key,value)
    return prefix+body


def pack(text,budget,*,prefix=''):
    if not text.startswith(prefix):raise ValueError('Prefix differs')
    report={'scheme':'exact_phrase_dictionary_v1','prefix':prefix,'dictionary':[],'expanded_characters':len(text),'encoded_characters':len(text),'roundtrip_exact':True}
    if len(text)<=budget:return text,report
    body=text[len(prefix):];pool=candidates(body);entries=[];encoded=text
    for key in (v for v in SYMBOLS if v not in text):
        choices=[]
        for phrase in pool:
            n=body.count(phrase)
            # Cost includes the new dictionary entry and separator, not tokenizer estimates.
            gain=n*(len(phrase)-len(key))-(len(key)+len(phrase)+2)
            if gain>0:choices.append((gain,len(phrase),phrase))
        if not choices:break
        _,_,phrase=max(choices);body=body.replace(phrase,key);entries.append([key,phrase]);pool.remove(phrase)
        header=LABEL+'；'.join(k+'='+v for k,v in entries)+'。\n';candidate=prefix+header+body
        if len(candidate)<len(encoded):encoded=candidate;report['dictionary']=[list(v) for v in entries]
        if len(encoded)<=budget:break
    report['encoded_characters']=len(encoded)
    if unpack(encoded,report)!=text:raise ValueError('Lossless packing round-trip failed')
    if len(encoded)>budget:raise ValueError(f'Complete prompt exceeds budget after lossless packing: {len(encoded)} > {budget}; no truncation')
    return encoded,report
