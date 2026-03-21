import json
import os
import math

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

# SGG to MOIS mapping helper (from run_server.py logic)
SIDO_MAP = {"11": "서울특별시", "23": "인천광역시", "28": "인천광역시", "31": "경기도", "41": "경기도"}

# Build dong_info for cached dongs
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

# Scoring Function (Mimic analyze_single_area in run_server.py)
def calculate_grade(adm_cd):
    info = dong_info.get(adm_cd)
    if not info: return None
    
    # 1. Academy Score (Revised 50:50)
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

    # 2. House/Apt Score
    hs = api_cache.get(f"house_stats_{adm_cd}_2022", {"ratio": 0})
    apt_ratio = hs.get('ratio', 0)
    apt_score = min(max(round((apt_ratio - 40) / 50 * 100), 0), 100)

    # 3. GPA Intensity (Simplified lookup)
    # Find matching school_db entry for this SGG
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

    # 4. School Balance & Students per High
    # (Default to 70 for simulation where data is missing)
    balance_score = 70 
    students_per_high_score = 70

    # Total Score (Weighted) 5/25/25/15/30
    total = round(
        balance_score * 0.05 + 
        students_per_high_score * 0.25 + 
        academy_score * 0.25 + 
        apt_score * 0.15 + 
        gpa_score * 0.30
    )
    
    grade = 'S+' if total >= 95 else 'A' if total >= 80 else 'B' if total >= 65 else 'C'
    return grade

# Execute Simulation
grade_counts = {'S+': 0, 'A': 0, 'B': 0, 'C': 0}
analyzed = 0
for adm_cd in dong_info.keys():
    g = calculate_grade(adm_cd)
    if g:
        grade_counts[g] += 1
        analyzed += 1

print(f"--- Analysis Status ---")
print(f"Total Dong Samples: {analyzed}")
print(json.dumps(grade_counts, indent=2))
