import json
import run_server

with open("schools_db.json", "r", encoding="utf-8") as f:
    db = json.load(f)

for code in ["28110", "41192", "41194", "41196"]:
    name = db[code]["name"]
    print(f"Fetching students for {name} ({code})")
    students = run_server.fetch_schoolinfo_students(code, name)
    db[code]["students"] = students
    print(f"  Found {len(students)} schools")

with open("schools_db.json", "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

print("\nUpdated schools_db.json with students data.")
