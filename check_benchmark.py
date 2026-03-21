import json, os

CACHE_FILE = "sgis_cache.json"
with open(CACHE_FILE, "r", encoding="utf-8") as f:
    cache = json.load(f)

# 캐시에 있는 데이터 중 학원수가 가장 많은 곳 상위 10개 추출 (이곳들이 주요 학군지)
counts = []
for k, v in cache.items():
    if k.startswith("comp_") and "_P855" in k:
        cd = k.split("_")[1]
        # 해당 코드의 인구를 찾음 (연도 무관)
        pop = 0
        for pk, pv in cache.items():
            if pk.startswith(f"pop_{cd}"):
                pop = pv
                break
        
        if pop > 0:
            density = v / (pop / 1000)
            score = min(round((density / 3.0) * 100), 100)
            counts.append({
                "cd": cd, "comp": v, "pop": pop, "dens": density, "score": score
            })

# 밀집도 순 정렬
counts.sort(key=lambda x: x['dens'], reverse=True)

print(f"{'코드':<12} | {'학원수':<6} | {'인구':<10} | {'1000명당 학원':<15} | {'학원점수'}")
print("-" * 75)
for c in counts[:15]:
    print(f"{c['cd']:<12} | {c['comp']:<9} | {c['pop']:<10} | {c['dens']:<18.2f} | {c['score']:>5}점")
