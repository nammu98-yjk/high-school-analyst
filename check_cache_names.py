import json
with open('sgis_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

for item in cache.get('stages_31', []):
    if item['cd'] == '31192':
        print(f"31192 in cache is: {item['addr_name']}")
    if item['cd'] == '31052':
        print(f"31052 in cache is: {item['addr_name']}")
