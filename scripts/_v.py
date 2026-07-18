import json
idx = json.loads(open(r'D:\github\agentcore-control-plane\.cursor\hooks\state\continual-learning-index.json', encoding='utf-8').read())
print('processedAtUtc:', idx['processedAtUtc'])
print('counts:', idx['counts'])
total = len(idx['transcripts'])
quarantined = [k for k,v in idx['transcripts'].items() if v.get('retrievalStatus')=='quarantined']
active = [k for k,v in idx['transcripts'].items() if v.get('retrievalStatus')=='active']
print(f'total entries: {total}  active: {len(active)}  quarantined: {len(quarantined)}')
print()
print('newest 5 by mtime:')
sorted_t = sorted(idx['transcripts'].items(), key=lambda kv: kv[1].get('mtimeUtc',''), reverse=True)[:5]
for k, v in sorted_t:
    print(f'  {v["mtimeUtc"]}  {k}')
print()
print('quarantined list:')
for k in quarantined:
    print(f'  {k}  ({idx["transcripts"][k].get("quarantineReason")})')
