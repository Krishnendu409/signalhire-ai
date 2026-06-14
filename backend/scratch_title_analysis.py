import asyncio
from validation_200 import RESUMES
from app.services.ai import AIPipeline, _normalize_title

async def analyze():
    errors = []
    for i, r in enumerate(RESUMES):
        parsed = await AIPipeline.parse_resume(r['text'])
        p_title = parsed.get('current_title', '')
        gt_title = r['gt']['title']
        
        if p_title != gt_title:
            errors.append({
                'id': i,
                'raw_text': r['text'][:100].replace('\n', ' '),
                'parsed': p_title,
                'expected': gt_title
            })
            
    for e in errors:
        print(f"{e['expected']} | {e['parsed']} | {e['raw_text']}")
    print(f'Total errors: {len(errors)}')

asyncio.run(analyze())
