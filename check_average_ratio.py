import json
import os

DIRECTORY = "c:\\Users\\82103\\OneDrive\\바탕 화면\\신학군지 추출 시스템"
CACHE_FILE = os.path.join(DIRECTORY, 'sgis_cache.json')
POP_DB_FILE = os.path.join(DIRECTORY, 'population_db.json')

if not os.path.exists(CACHE_FILE) or not os.path.exists(POP_DB_FILE):
    print("Required files missing.")
    exit()

with open(CACHE_FILE, 'r', encoding='utf-8') as f:
    api_cache = json.load(f)
with open(POP_DB_FILE, 'r', encoding='utf-8') as f:
    pop_db = json.load(f)

# Extract academy counts from cache (Key: "company_{adm_cd}_P855_2023")
academy_data = {}
for k, v in api_cache.items():
    if k.startswith("company_") and "_P855_" in k:
        # Extract adm_cd
        parts = k.split("_")
        adm_cd = parts[1]
        academy_data[adm_cd] = v

print(f"Total Cached Dongs with academy data: {len(academy_data)}")

# Map adm_cd to pop_db (This is tricky as SGIS vs MOIS codes differ)
# But we can try name-based matching if we had names for the cached dongs.
# The cache doesn't store names. 

# Let's try to calculate from the last few analysis runs or some known codes.
# Actually, let's just use the benchmark from the code: 10.0 per 100 students is 100 points.
# Average is likely around 1~3 per 100 students.

# Better yet, let's fetch a few major dongs to show real examples.
major_areas = [
    {"sido": "서울특별시", "sgg": "강남구", "dong": "대치1동", "adm_cd": "1123072"}, # Mock SGIS cd
    {"sido": "경기도", "sgg": "성남시 분당구", "dong": "정자1동"},
    {"sido": "경기도", "sgg": "안양시 동안구", "dong": "범계동"},
    {"sido": "서울특별시", "sgg": "양천구", "dong": "목5동"},
    {"sido": "경기도", "sgg": "군포시", "dong": "산본1동"}
]

# I'll just calculate a quick average from the current cache if possible.
ratios = []
for adm_cd, count in academy_data.items():
    # If the adm_cd is 10 digits, we might find it in pop_db's 'code' field
    # But SGIS 10 digits and MOIS 10 digits are different.
    # Let's see if we can identify any by 'total_students'
    pass

print("\n--- Summary of current benchmark ---")
print("점수 산출 기준: 학생 100명당 학원 10개 이상 = 100점")
print("즉, 학생 10명당 학원 1개 수준이 최상위권입니다.")
