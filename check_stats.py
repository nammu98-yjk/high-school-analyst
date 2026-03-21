import json
import os

DIRECTORY = "c:\\Users\\82103\\OneDrive\\바탕 화면\\신학군지 추출 시스템"
CACHE_FILE = os.path.join(DIRECTORY, 'sgis_cache.json')
POP_DB_FILE = os.path.join(DIRECTORY, 'population_db.json')

with open(CACHE_FILE, 'r', encoding='utf-8') as f:
    api_cache = json.load(f)
with open(POP_DB_FILE, 'r', encoding='utf-8') as f:
    pop_db = json.load(f)

# Build a mapping of SGIS CD (starts with 11, 23, 28, 31, 41) to Name
# by searching for stages_ keys in cache
cd_to_name = {}
for k, v in api_cache.items():
    if k.startswith("stages_"):
        if isinstance(v, list):
            for item in v:
                if 'cd' in item and 'addr_name' in item:
                    cd_to_name[item['cd']] = item['addr_name']

# Find all 10-digit codes (Dongs) and their names
# We'll need the district name too.
dong_info = {}
for k, v in api_cache.items():
    if k.startswith("stages_") and len(k) > 7: # stages_ prefix + sgg_cd (5 digits)
        sgg_cd = k.replace("stages_", "")
        sgg_name = cd_to_name.get(sgg_cd, "")
        if isinstance(v, list):
            for item in v:
                dong_info[item['cd']] = {"name": item['addr_name'], "sgg": sgg_name}

# Calculate Ratios for cached dongs
results = []
SIDO_MAP = {"11": "서울특별시", "23": "인천광역시", "28": "인천광역시", "31": "경기도", "41": "경기도"}

for k, v in api_cache.items():
    if k.startswith("company_") and "_P855_" in k:
        parts = k.split("_")
        adm_cd = parts[1]
        academy_count = v
        
        info = dong_info.get(adm_cd)
        if info:
            dong_name = info['name']
            sgg_name = info['sgg']
            sido_nm = SIDO_MAP.get(adm_cd[:2], "경기도")
            
            # Match with pop_db
            search_key = f"{sido_nm} {sgg_name} {dong_name}"
            pop_data = pop_db.get(search_key)
            if not pop_data:
                # Try partial match for Gyeonggi
                matches = [pk for pk in pop_db.keys() if pk.startswith(sido_nm) and pk.endswith(dong_name) and sgg_name in pk]
                if matches:
                    pop_data = pop_db[matches[0]]
            
            if pop_data and pop_data['total_students'] > 0:
                ratio = academy_count / (pop_data['total_students'] / 100)
                results.append({"name": f"{sgg_name} {dong_name}", "ratio": ratio, "students": pop_data['total_students'], "academies": academy_count})

if results:
    avg_ratio = sum(r['ratio'] for r in results) / len(results)
    results.sort(key=lambda x: x['ratio'], reverse=True)
    
    print(f"Stats for {len(results)} cached dongs:")
    print(f"Average ratio: {avg_ratio:.2f} academies per 100 students")
    print("\nTop 5 Areas:")
    for r in results[:5]:
        print(f" - {r['name']}: {r['ratio']:.2f} (Students:{r['students']}, Academies:{r['academies']})")
    
    # Random selection or median for "Normal"
    mid = len(results) // 2
    print(f"\nMedian Area:")
    print(f" - {results[mid]['name']}: {results[mid]['ratio']:.2f}")
else:
    print("No matching data found in cache.")
