# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from run_server import fetch_json, SCHOOL_API_KEY

SIDO, SGG = "11", "11680"

print("=== apiType=06 모든 연도 + apiType 01~07 모든 조합 탐색 ===\n")

# apiType=06의 최신 공시 연도 찾기 (졸업생 진로는 보통 전전년도 기준)
print("[apiType=06 연도 탐색]")
for year in ["2024", "2023", "2022"]:
    for knd in ["04"]:
        url = (f"https://www.schoolinfo.go.kr/openApi.do"
               f"?apiKey={SCHOOL_API_KEY}&apiType=06&pbanYr={year}"
               f"&schulKndCode={knd}&sidoCode={SIDO}&sggCode={SGG}")
        data = fetch_json(url)
        if not data: continue
        rc = data.get("resultCode")
        msg = data.get("resultMsg", "")
        items = data.get("list", [])
        print(f"  {year}년: {rc} / {len(items)}건 / {msg[:60]}")

# apiType 01~07 중학교로 새 탐색 (고교는 전부 fail이었으나 중학교는 다를 수 있음)
print("\n[apiType 01~07 고교 pbanYr 없이 시도]")
for t in ["01","02","03","04","05","06","07"]:
    url = (f"https://www.schoolinfo.go.kr/openApi.do"
           f"?apiKey={SCHOOL_API_KEY}&apiType={t}"
           f"&schulKndCode=04&sidoCode={SIDO}&sggCode={SGG}")
    data = fetch_json(url)
    if not data: continue
    rc = data.get("resultCode")
    items = data.get("list", [])
    if items:
        print(f"  ✅ apiType={t} (연도 없음): {len(items)}건! 키={list(items[0].keys())[:8]}")
    else:
        print(f"  apiType={t}: {rc} / {data.get('resultMsg','')[:50]}")

# 졸업생 진로 pbanYr 없이 다른 파라미터 조합
print("\n[apiType=06 파라미터 변형 시도]")
combos = [
    {"apiKey": SCHOOL_API_KEY, "apiType": "06", "schulKndCode": "04", "ATPT_OFCDC_SC_CODE": "B10"},
    {"apiKey": SCHOOL_API_KEY, "apiType": "06", "schulKndCode": "04", "sidoCode": SIDO},
    {"apiKey": SCHOOL_API_KEY, "apiType": "06", "schulKndCode": "04", "sidoCode": SIDO, "sggCode": SGG, "pbanYr": "2023", "DGHT_CRSE_SC_CODE": "02"},
    {"apiKey": SCHOOL_API_KEY, "apiType": "06", "schulKndCode": "04", "sidoCode": "11", "pbanYr": "2023"},
]
import urllib.parse
for combo in combos:
    url = "https://www.schoolinfo.go.kr/openApi.do?" + urllib.parse.urlencode(combo)
    data = fetch_json(url)
    if not data: continue
    rc = data.get("resultCode")
    items = data.get("list", [])
    if items:
        print(f"  ✅ 성공! {combo}")
        print(f"     키: {list(items[0].keys())[:10]}")
    else:
        print(f"  {rc}: {data.get('resultMsg','')[:60]}")
