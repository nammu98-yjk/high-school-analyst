import os, json
import importlib.util

# Load run_server.py as a module
spec = importlib.util.spec_from_file_location("run_server", "c:\\Users\\82103\\OneDrive\\바탕 화면\\신학군지 추출 시스템\\run_server.py")
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)

# Test analyize for Sosa-gu dong
# 괴안동 (31192520)
adm_cd = "31192520"
name = "괴안동"

print(f"--- Mock Analysis for {name} ({adm_cd}) ---")
res = rs.analyze_single_area(adm_cd, name)
print(json.dumps(res, ensure_ascii=False, indent=2))
