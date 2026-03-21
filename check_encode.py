import json

with open('sgis_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

output = []
for item in cache.get('stages_31', []):
    if item['cd'] in ['31051', '31052', '31053', '31190', '31191', '31192', '31193']:
        output.append(f"{item['cd']} : {item['addr_name']}")

with open('cache_test_out.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
