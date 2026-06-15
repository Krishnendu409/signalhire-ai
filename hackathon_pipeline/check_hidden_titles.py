import json

titles = ['revenue operations manager', 'customer success manager', 'enterprise account executive', 'territory manager', 'gtm lead', 'sales executive']
counts = {t: 0 for t in titles}

path = r"C:\Users\krish\Downloads\signalhire-ai-master (3)\signalhire-ai-master\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"

with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            title = data.get('current_title', '')
            if title:
                title = title.lower()
                for t in titles:
                    if t in title:
                        counts[t] += 1
        except:
            pass

print("Title Counts:")
for t, c in counts.items():
    print(f"  {t}: {c}")
