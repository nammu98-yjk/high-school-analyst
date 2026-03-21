import json, os, sys

# run_server.py의 캐시 포맷
# comp_{adm_cd}_{biz_cd}_{year}
# pop_{adm_cd}_{year}

def calculate_score(academy, population):
    if population <= 0: return 0
    density = academy / (population / 1000 + 0.1)
    score = min(round((density / 3.0) * 100), 100)
    return density, score

cache_path = "sgis_cache.json"
if not os.path.exists(cache_path):
    print("캐시 파일이 없습니다.")
    sys.exit()

with open(cache_path, "r", encoding="utf-8") as f:
    cache = json.load(f)

# adm_cd별로 매칭 (P855=학원, pop=인구)
extracted = {}
for key, val in cache.items():
    if key.startswith("comp_") and "_P855" in key:
        # comp_11680_P855_2023 -> 11680
        parts = key.split("_")
        adm_cd = parts[1]
        if adm_cd not in extracted: extracted[adm_cd] = {"academy": 0, "pop": 0}
        extracted[adm_cd]["academy"] = val
    elif key.startswith("pop_"):
        # pop_11680_2023 -> 11680
        parts = key.split("_")
        adm_cd = parts[1]
        if adm_cd not in extracted: extracted[adm_cd] = {"academy": 0, "pop": 0}
        extracted[adm_cd]["pop"] = val

results = []
for cd, d in extracted.items():
    if d["pop"] > 0 and d["academy"] > 0:
        density, score = calculate_score(d["academy"], d["pop"])
        results.append({
            "cd": cd, "academy": d["academy"], "pop": d["pop"], "density": density, "score": score
        })

results.sort(key=lambda x: x['density'], reverse=True)

print("=== 주요 지역 학원 밀집도 및 점수 계산 내역 (수집된 캐시 데이터 기준) ===")
print(f"{'코드':<10} | {'학원수':<6} | {'인구':<8} | {'1,000명당 학원수':<15} | {'학원점수':<6}")
print("-" * 75)

for r in results[:20]:
     print(f"{r['cd']:<10} | {r['academy']:<7} | {r['pop']:<8} | {r['density']:<18.2f} | {r['score']:<6}")

print("\n* 밀집도가 3.0 이상일 경우 100점 만점이 부여됩니다.")
