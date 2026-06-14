import pandas as pd
import re

series = pd.Series(["I am a search engineer", "nothing here", "search and relevance search"])
terms = ["search", "relevance", "engineer"]

def orig(series, terms):
    hits = pd.Series(0, index=series.index)
    for w in terms:
        hits += series.str.contains(r'\b' + re.escape(w.lower()) + r'\b', regex=True, case=False).astype(int)
    return hits

def opt(series, terms):
    pattern = r'\b(?:' + '|'.join(re.escape(w.lower()) for w in sorted(terms, key=len, reverse=True)) + r')\b'
    return series.str.findall(pattern, flags=re.IGNORECASE).apply(lambda x: len(set([w.lower() for w in x])) if isinstance(x, list) else 0)

print("Original:")
print(orig(series, terms))
print("Optimized:")
print(opt(series, terms))
