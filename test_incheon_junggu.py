import os, json
import importlib.util

spec = importlib.util.spec_from_file_location("run_server", "c:\\Users\\82103\\OneDrive\\바탕 화면\\신학군지 추출 시스템\\run_server.py")
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)

adm_cd = "23010530" # Shinpoh-dong? Not sure, let's just test analyze_single_area
name = "신포동"

print(f"--- Mock Analysis for {name} ({adm_cd}) ---")
res = rs.analyze_single_area(adm_cd, name)
print(json.dumps({
    "grade": res.get("grade"),
    "schools_count": len(res.get("schoolsRaw", [])),
    "schoolsRaw": res.get("schoolsRaw", []),
}, ensure_ascii=False, indent=2))
