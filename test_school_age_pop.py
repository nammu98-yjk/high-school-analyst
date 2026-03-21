"""
공공데이터포털 연령별 인구 API 상세 확인
"""
import json, urllib.request, urllib.parse, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

NEW_KEY = 'adcbb74b26d7f4f80ae4068bba6112d4689cccdc5a8d7ee6594717aeeb26409f'

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
            raw = r.read()
            try:
                return json.loads(raw.decode('utf-8'))
            except:
                return json.loads(raw.decode('cp949'))
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
        return None

# ===== 공공데이터포털 API - 첫 번째 row 전체 필드 확인 =====
print("===== 필드명 전체 확인 (강남구 등 특정 지역 필터) =====")
ENDPOINT = "https://api.odcloud.kr/api/15097972/v1/uddi:a7a3e616-d680-42b9-ae74-f2c5d012da36"
url = f"{ENDPOINT}?serviceKey={NEW_KEY}&page=1&perPage=1&returnType=JSON"
data = fetch_json(url)
if data:
    print(f"총 데이터 수: {data.get('totalCount')}")
    if data.get('data'):
        sample = data['data'][0]
        print(f"필드 목록:")
        for k, v in sample.items():
            print(f"  '{k}': {v}")

# ===== perPage를 늘려서 데이터 내용 파악 =====
print("\n===== 총 5행 조회 =====")
url2 = f"{ENDPOINT}?serviceKey={NEW_KEY}&page=1&perPage=5&returnType=JSON"
data2 = fetch_json(url2)
if data2 and data2.get('data'):
    for row in data2['data']:
        # 13~18세 합산
        mid_students = sum(row.get(f'{i}세', row.get(f'{i}세 ', 0)) for i in range(13, 16))
        high_students = sum(row.get(f'{i}세', row.get(f'{i}세 ', 0)) for i in range(16, 19))
        print(f"  행: {list(row.items())[:5]}")
        
# ===== 필터 파라미터 탐색 =====
print("\n===== 필터 시도 (cond 파라미터) =====")
# cond[행정구역코드::EQ]=11680 등 시도
url3 = f"{ENDPOINT}?serviceKey={NEW_KEY}&page=1&perPage=5&returnType=JSON&cond%5B%ED%96%89%EC%A0%95%EA%B5%AC%EC%97%AD%EC%BD%94%EB%93%9C%3A%3AEQ%5D=11680"
data3 = fetch_json(url3)
if data3:
    print(f"  cond 응답: {str(data3)[:300]}")

# SGIS 연령별 인구 API 정확한 파라미터 재시도
print("\n===== SGIS population.json 실제 응답 필드 확인 =====")
SGIS_KEY = 'b9f5f345dcd24b989899'
SGIS_SECRET = 'f35f7ef12a774550be0e'
auth_url = f"https://sgisapi.kostat.go.kr/OpenAPI3/auth/authentication.json?consumer_key={SGIS_KEY}&consumer_secret={SGIS_SECRET}"
auth_data = fetch_json(auth_url)
token = auth_data['result']['accessToken']

# 강남구 인구 (11680 = 구단위)
for adm_cd, name in [("11680", "강남구"), ("4113500000", "분당구")]:
    url_p = f"https://sgisapi.kostat.go.kr/OpenAPI3/stats/population.json?accessToken={token}&adm_cd={adm_cd}&year=2023&low_search=0"
    d = fetch_json(url_p)
    if d and d.get('errCd') == 0:
        r = d['result'][0] if d.get('result') else {}
        print(f"[{name}] population keys: {list(r.keys())}")
        print(f"  데이터: {r}")
