import json
import os

# Load all required DBs and Caches
DIRECTORY = "c:\\Users\\82103\\OneDrive\\바탕 화면\\신학군지 추출 시스템"
CACHE_FILE = os.path.join(DIRECTORY, 'sgis_cache.json')
POP_DB_FILE = os.path.join(DIRECTORY, 'population_db.json')
SCHOOLS_DB_FILE = os.path.join(DIRECTORY, 'schools_db.json')

with open(CACHE_FILE, 'r', encoding='utf-8') as f:
    api_cache = json.load(f)
with open(POP_DB_FILE, 'r', encoding='utf-8') as f:
    pop_db = json.load(f)
with open(SCHOOLS_DB_FILE, 'r', encoding='utf-8') as f:
    schools_db = json.load(f)

# SGG to MOIS mapping helper
SIDO_MAP = {"11": "서울특별시", "23": "인천광역시", "28": "인천광역시", "31": "경기도", "41": "경기도"}

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

def calculate_score(adm_cd):
    info = dong_info.get(adm_cd)
    if not info: return None
    academy = api_cache.get(f"company_{adm_cd}_P855_2023", 0)
    sido_nm = SIDO_MAP.get(adm_cd[:2], "경기도")
    sgg_name = info['sgg']
    area_name = info['name']
    search_key = f"{sido_nm} {sgg_name} {area_name}"
    pop_data = pop_db.get(search_key)
    if not pop_data:
        matches = [pk for pk in pop_db.keys() if pk.startswith(sido_nm) and pk.endswith(area_name) and sgg_name in pk]
        if matches: pop_data = pop_db[matches[0]]
    if not pop_data or pop_data['total_students'] == 0: return None
    students = pop_data['total_students']
    ratio = academy / (students / 100)
    score_rel = min(round((ratio / 4.0) * 100), 100)
    score_abs = min(round((academy / 100) * 100), 100)
    academy_score = round(score_rel * 0.5 + score_abs * 0.5)
    hs = api_cache.get(f"house_stats_{adm_cd}_2022", {"ratio": 0})
    apt_ratio = hs.get('ratio', 0)
    apt_score = min(max(round((apt_ratio - 40) / 50 * 100), 0), 100)
    elite_rate = -1
    std_dev = 0
    search_sgg = sgg_name.replace(" ", "")
    for entry in schools_db.values():
        if search_sgg in entry.get("name", "").replace(" ", ""):
            stats = entry.get("elite_stats", {})
            elite_rate = stats.get("elite_rate", -1)
            high_gpa = entry.get("high_gpa", {})
            std_dev = high_gpa.get('mean_std_dev', 0)
            break
    gpa_score = 0
    if elite_rate >= 0:
        score_a = max(0, min(100, 100 - (elite_rate / 12.0) * 100))
        score_b = max(0, min(100, (std_dev - 12) / 8.0 * 100)) if std_dev > 0 else 0
        gpa_score = round(score_a * 0.5 + score_b * 0.5) if std_dev > 0 else round(score_a)
    balance_score = 70 
    sh_score = 70
    total = round(balance_score * 0.05 + sh_score * 0.25 + academy_score * 0.25 + apt_score * 0.15 + gpa_score * 0.30)
    return total

all_scores = []
for adm_cd in dong_info.keys():
    s = calculate_score(adm_cd)
    if s: all_scores.append(s)

all_scores.sort(reverse=True)
count = len(all_scores)

if count > 0:
    print(f"Total analyzed: {count}")
    # Percentiles: S:4, A:11, B:23, C:40, D:60
    p4 = all_scores[max(0, int(count * 0.04) - 1)]
    p11 = all_scores[max(0, int(count * 0.11) - 1)]
    p23 = all_scores[max(0, int(count * 0.23) - 1)]
    p40 = all_scores[max(0, int(count * 0.40) - 1)]
    p60 = all_scores[max(0, int(count * 0.60) - 1)]
    
    thresholds = {"S": p4, "A": p11, "B": p23, "C": p40, "D": p60}
    print(json.dumps(thresholds, indent=2))
