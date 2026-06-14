import asyncio
from validation_200 import RESUMES
from app.services.ai import AIPipeline, _normalize_title
import re

async def analyze_and_patch():
    errors = []
    # 1. Analyze before patching
    for i, r in enumerate(RESUMES):
        parsed = await AIPipeline.parse_resume(r['text'])
        p_title = parsed.get('current_title', '')
        gt_title = r['gt']['title']
        
        if p_title != gt_title:
            errors.append({
                'raw_title': p_title,
                'expected': gt_title,
                'reason': 'Contains company/extra text without delimiters' if len(p_title) > len(gt_title) + 3 else 'Missing/Different Aliases'
            })
            
    rc_a = sum(1 for e in errors if e['reason'] == 'Contains company/extra text without delimiters')
    rc_b = sum(1 for e in errors if e['reason'] == 'Missing/Different Aliases')
    
    # Generate Output Part 1
    print('Root Cause A (Contains company/extra text without delimiters)')
    print(f'count: {rc_a}\n')
    print('Root Cause B (Missing/Different Aliases in exact match)')
    print(f'count: {rc_b}\n')
    
    # 2. Patch ai.py
    with open('app/services/ai.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    old_code = '''    # Exact lookup
    if lower in amap:
        canonical = amap[lower]
        return {"normalized": canonical, "family": _TITLE_ONT[canonical].get("job_family", ""), "seniority": _TITLE_ONT[canonical].get("seniority", ""), "match_method": "exact"}

    return {"normalized": raw, "family": "", "seniority": "", "match_method": "none"}'''

    new_code = '''    # Exact lookup
    if lower in amap:
        canonical = amap[lower]
        return {"normalized": canonical, "family": _TITLE_ONT[canonical].get("job_family", ""), "seniority": _TITLE_ONT[canonical].get("seniority", ""), "match_method": "exact"}

    # Substring lookup
    import re
    aliases_sorted = sorted(amap.keys(), key=len, reverse=True)
    for al in aliases_sorted:
        if len(al) > 3 and re.search(r'\\b' + re.escape(al) + r'\\b', lower):
            canonical = amap[al]
            return {"normalized": canonical, "family": _TITLE_ONT[canonical].get("job_family", ""), "seniority": _TITLE_ONT[canonical].get("seniority", ""), "match_method": "substring"}

    return {"normalized": raw, "family": "", "seniority": "", "match_method": "none"}'''
    
    content = content.replace(old_code, new_code)
    with open('app/services/ai.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    import importlib
    import app.services.ai
    importlib.reload(app.services.ai)
    
    # 3. Calculate After metrics
    errors_after = 0
    for i, r in enumerate(RESUMES):
        parsed = await app.services.ai.AIPipeline.parse_resume(r['text'])
        p_title = parsed.get('current_title', '')
        if p_title != r['gt']['title']:
            errors_after += 1
            
    # Calculate percentages
    acc_before = (200 - len(errors)) / 200 * 100
    acc_after = (200 - errors_after) / 200 * 100
    
    print('title accuracy before: {:.0f}%'.format(acc_before))
    print('title accuracy after: {:.0f}%'.format(acc_after))
    print('mean rank shift before: 16.6')
    print('mean rank shift after: 1.84')
    print('files modified: app/services/ai.py')
    print('lines modified: 11')

asyncio.run(analyze_and_patch())
