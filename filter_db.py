import json, os
def filter_json(path, condition):
    if not os.path.exists(path):
        print(f"Skipping {path}: not found")
        return
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    filtered = {k: v for k, v in data.items() if condition(k, v)}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False)
    print(f"Filtered {path}: {len(data)} -> {len(filtered)}")

p1 = 'functions/db/population_db.json'
p2 = 'functions/db/schools_db.json'

filter_json(p1, lambda k, v: any(x in k for x in ['서울', '인천', '경기']))
filter_json(p2, lambda k, v: k[:2] in ['11', '23', '28', '31', '41'])
