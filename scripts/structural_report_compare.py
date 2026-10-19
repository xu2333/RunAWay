"""Exact structural-report comparison except a bounded derived macro rounding.

Both macro values must agree with the exact rational mean of integer cluster
counts within2ULPs. Every integer, identity, field and other value stays exact.
"""
from fractions import Fraction
import math


def compare(expected, actual):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or expected.keys()!=actual.keys():raise ValueError('Report fields changed')
        for key,value in expected.items():
            if key=='macro_cluster_accuracy':
                clusters=expected['paired_clusters'];rational=sum((Fraction(c['correct'],c['planned']) for c in clusters),Fraction())/len(clusters)
                reference=float(rational)
                for candidate in (value,actual[key]):
                    if type(candidate) is not float or not math.isfinite(candidate) or abs(candidate-reference)>2*math.ulp(reference):
                        raise ValueError('Macro mean disagrees with exact integer ratios')
            else:compare(value,actual[key])
    elif isinstance(expected,list):
        if not isinstance(actual,list) or len(expected)!=len(actual):raise ValueError('Report list changed')
        for a,b in zip(expected,actual):compare(a,b)
    elif expected!=actual:raise ValueError('Exact report value changed')
