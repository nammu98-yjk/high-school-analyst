import json, urllib.request, urllib.parse, ssl, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

API_KEY = 'adcbb74b26d7f4f80ae4068bba6112d4689cccdc5a8d7ee6594717aeeb26409f'
ENDPOINT = "https://api.odcloud.kr/api/15097972/v1/uddi:a7a3e616-d680-42b9-ae74-f2c5d012da36"

# Population by age (Male/Female)
# Fields: "13세남자", "13세여자", ...
# Geofields: "시도명", "시군구명", "읍면동명"

def fetch_all_population():
    all_data = []
    page = 1
    per_page = 1000
    
    while True:
        print(f"Fetching page {page}...")
        url = f"{ENDPOINT}?serviceKey={API_KEY}&page={page}&perPage={per_page}&returnType=JSON"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
            with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
                data = json.loads(r.read().decode('utf-8'))
                rows = data.get("data", [])
                if not rows:
                    break
                all_data.extend(rows)
                if len(rows) < per_page:
                    break
                page += 1
                time.sleep(0.5) # Avoid rate limiting
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
            
    return all_data

if __name__ == "__main__":
    pop_data = fetch_all_population()
    print(f"Total rows fetched: {len(pop_data)}")
    
    # Process and save a structured version
    # Key: "City District Dong" for easy matching
    structured_db = {}
    for row in pop_data:
        sido = row.get("시도명", "")
        sgg = row.get("시군구명", "")
        dong = row.get("읍면동명", "")
        
        # Clean up names (remove trailing spaces or dots if any)
        sido = sido.strip() if sido else ""
        sgg = sgg.strip() if sgg else ""
        dong = dong.strip() if dong else ""
        
        # Calculate Middle/High age population
        # Middle school age: 13, 14, 15
        # High school age: 16, 17, 18
        mid_pop = 0
        high_pop = 0
        for age in range(13, 16):
            mid_pop += int(row.get(f"{age}세남자", 0)) + int(row.get(f"{age}세여자", 0))
        for age in range(16, 19):
            high_pop += int(row.get(f"{age}세남자", 0)) + int(row.get(f"{age}세여자", 0))
            
        key = f"{sido} {sgg} {dong}".strip()
        structured_db[key] = {
            "mid_pop": mid_pop,
            "high_pop": high_pop,
            "total_students": mid_pop + high_pop,
            "total_pop": int(row.get("계", 0)),
            "sido": sido,
            "sgg": sgg,
            "dong": dong,
            "code": row.get("행정기관코드")
        }
        
    with open('population_db.json', 'w', encoding='utf-8') as f:
        json.dump(structured_db, f, ensure_ascii=False, indent=2)
    print("Saved to population_db.json")
