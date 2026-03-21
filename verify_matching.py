import sys
import os
import json

# Mocking the environment for run_server.py
DIRECTORY = "c:\\Users\\82103\\OneDrive\\바탕 화면\\신학군지 추출 시스템"
POP_DB_FILE = os.path.join(DIRECTORY, 'population_db.json')
POPULATION_DB = {}
if os.path.exists(POP_DB_FILE):
    with open(POP_DB_FILE, 'r', encoding='utf-8') as f:
        POPULATION_DB = json.load(f)

def test_match(sido_prefix, district_name, area_name):
    sido_nm = {"11": "서울특별시", "23": "인천광역시", "28": "인천광역시", "31": "경기도"}.get(sido_prefix, "경기도")
    
    # DB 매칭 시도
    search_key = f"{sido_nm} {district_name} {area_name}"
    pop_data = POPULATION_DB.get(search_key)
    match_type = "Direct"

    if not pop_data:
        matches = [k for k in POPULATION_DB.keys() if k.startswith(sido_nm) and k.endswith(area_name) and district_name in k]
        if matches:
            pop_data = POPULATION_DB[matches[0]]
            search_key = matches[0]
            match_type = "Regex/Partial"

    if pop_data:
        print(f"Match Found [{match_type}]: {search_key} -> Students: {pop_data['total_students']}")
    else:
        print(f"No match for: {sido_nm} | {district_name} | {area_name}")

# Test Cases
print("--- Bundang ---")
test_match("31", "분당구", "정자1동") # Should find "경기도 성남시 분당구 정자1동"
print("\n--- Gangnam ---")
test_match("11", "강남구", "대치1동") # Should find "서울특별시 강남구 대치1동"
print("\n--- Gunpo ---")
test_match("31", "군포시", "산본1동") # Should find "경기도 군포시 산본1동"
