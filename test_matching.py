import json

with open('population_db.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

# Testing matching for a few sample cases
cases = [
    {"sido": "11", "sgg": "강남구", "dong": "삼성1동"},
    {"sido": "31", "sgg": "덕양구", "dong": "화정1동"},
    {"sido": "31", "sgg": "수지구", "dong": "풍덕천1동"},
    {"sido": "23", "sgg": "부평구", "dong": "부평1동"}
]

SIDO_MAP = {"11": "서울특별시", "23": "인천광역시", "28": "인천광역시", "31": "경기도", "41": "경기도"}

print("--- Testing Matching ---")
for c in cases:
    sido_nm = SIDO_MAP.get(c['sido'])
    sgg_nm = c['sgg']
    dong_nm = c['dong']
    
    # Try direct match
    key = f"{sido_nm} {sgg_nm} {dong_nm}"
    data = db.get(key)
    
    # If no match, try finding sgg_nm in the mid-part of keys
    if not data:
        # Search for any key that starts with sido_nm and ends with dong_nm and contains sgg_nm
        matches = [k for k in db.keys() if k.startswith(sido_nm) and k.endswith(dong_nm) and sgg_nm in k]
        if matches:
            key = matches[0]
            data = db[key]
            print(f"[{c['sido']}-{c['sgg']}-{c['dong']}] Found: {key} -> {data['total_students']}")
        else:
            print(f"[{c['sido']}-{c['sgg']}-{c['dong']}] Not Found.")
    else:
        print(f"[{c['sido']}-{c['sgg']}-{c['dong']}] Direct Match: {key} -> {data['total_students']}")
