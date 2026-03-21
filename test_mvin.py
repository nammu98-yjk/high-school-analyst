# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from run_server import fetch_json, SCHOOL_API_KEY

# 검단신도시는 인천 서구(28260)에 위치
# 인천 시도코드: SGIS=23, 표준=28
tests = [
    ("28260", "서구(인천)", "28"),         # 검단 포함 인천 서구 전체
    ("28110", "중구(인천)", "28"),         # 인천 구도심
    ("28200", "부평구", "28"),
    ("11680", "강남구", "11"),             # 비교 기준
    ("41590", "화성시(동탄)", "41"),       # 신도시 비교
]

print("=== 신도시 vs 기성학군 순유입률 비교 ===\n")
for sgg_code, name, sido in tests:
    url = (f"https://www.schoolinfo.go.kr/openApi.do"
           f"?apiKey={SCHOOL_API_KEY}&apiType=10&pbanYr=2023"
           f"&schulKndCode=02&sidoCode={sido}&sggCode={sgg_code}")
    data = fetch_json(url)
    items = data.get('list', [])
    if items:
        total_in  = sum(i.get('MVIN_SUM',  0) for i in items)
        total_out = sum(i.get('MVT_SUM',   0) for i in items)
        total_st  = sum(i.get('STDNT_SUM', 0) for i in items)
        net = (total_in - total_out) / max(total_st, 1) * 100
        score = max(0, min(round(net / 5.0 * 100), 100))
        print(f"  {name:15s}: 전입{total_in:5d} 전출{total_out:5d} 총{total_st:6d} | 순유입{net:+.2f}% → {score:3d}점")
    else:
        print(f"  {name:15s}: 데이터 없음 ({data.get('resultCode')})")
