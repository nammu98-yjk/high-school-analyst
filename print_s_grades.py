import json
import run_server

with open("sgis_cache.json", "r", encoding="utf-8") as f:
    api_cache = json.load(f)

cd_to_name = {}
for k, v in api_cache.items():
    if k.startswith("stages_"):
        if isinstance(v, list):
            for item in v:
                cd_to_name[item['cd']] = item['addr_name']

dong_info = {}
for k, v in api_cache.items():
    if k.startswith("stages_") and len(k) > 7:
        sgg_cd = k.replace("stages_", "")
        sgg_name = cd_to_name.get(sgg_cd, "")
        if isinstance(v, list):
            for item in v:
                dong_info[item['cd']] = {"name": item['addr_name'], "sgg": sgg_name}

s_grades = []
for adm_cd, info in dong_info.items():
    # Only try to analyze if academy data exists in cache to run faster
    if f"company_{adm_cd}_P855_2023" in api_cache:
        res = run_server.analyze_single_area(adm_cd, info['name'])
        if res['totalScore'] >= 74:
            s_grades.append((res['totalScore'], info['sgg'], res['name']))

s_grades.sort(reverse=True)
print("--- S등급 지역 목록 ---")
for t in s_grades:
    print(f"{t[1]} {t[2]}: {t[0]}점")
