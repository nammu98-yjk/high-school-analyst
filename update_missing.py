import json
import crawl_apt2_elite
import crawl_apt2_high

missing = {
    "28110": "인천 중구",
    "41192": "부천시 원미구",
    "41194": "부천시 소사구",
    "41196": "부천시 오정구"
}

with open("schools_db.json", "r", encoding="utf-8") as f:
    db = json.load(f)

for code, name in missing.items():
    if code not in db:
        db[code] = {"name": name, "students": [], "achievement": 0}
    
    # apt2.me
    print(f"Fetching Elite info for {name} ({code})")
    elite = crawl_apt2_elite.fetch_apt2_data(code)
    if elite and "error" not in elite:
        db[code]["elite_stats"] = elite
        print(f"  Elite Rate: {elite['elite_rate']}%")
        
    print(f"Fetching High GPA info for {name} ({code})")
    high = crawl_apt2_high.fetch_apt2_high(code)
    if high and "error" not in high:
        db[code]["high_gpa"] = high
        print(f"  A-Rate: {high['mean_a_rate']}%, StdDev: {high['mean_std_dev']}")

with open("schools_db.json", "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

print("\nUpdated schools_db.json successfully.")
