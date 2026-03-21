import json, urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

SGIS_KEY = 'b9f5f345dcd24b989899'
SGIS_SECRET = 'f35f7ef12a774550be0e'

def get_token():
    auth_url = f"https://sgisapi.kostat.go.kr/OpenAPI3/auth/authentication.json?consumer_key={SGIS_KEY}&consumer_secret={SGIS_SECRET}"
    with urllib.request.urlopen(auth_url, context=ctx) as r:
        return json.loads(r.read())['result']['accessToken']

def fetch_data(token, adm_cd):
    pop = 0
    # 인구 수집 (2022 -> 2021 순서로 시도)
    for yr in ['2022', '2021']:
        url = f"https://sgisapi.kostat.go.kr/OpenAPI3/stats/population.json?accessToken={token}&adm_cd={adm_cd}&year={yr}&low_search=0"
        with urllib.request.urlopen(url, context=ctx) as r:
            res = json.loads(r.read())
            if res.get('errCd') == 0:
                 pop = int(res['result'][0]['tot_ppltn'])
                 break
    
    comp = 0
    # 학원 수집 (2021 -> 2020 순서로 시도)
    for yr in ['2021', '2020']:
        url = f"https://sgisapi.kostat.go.kr/OpenAPI3/stats/company.json?accessToken={token}&adm_cd={adm_cd}&year={yr}&class_code=P855&low_search=0"
        with urllib.request.urlopen(url, context=ctx) as r:
            res = json.loads(r.read())
            if res.get('errCd') == 0:
                 comp = int(res['result'][0]['corp_cnt'])
                 break
    return pop, comp

token = get_token()
samples = [
    {"name": "강남구", "cd": "11680"},
    {"name": "양천구", "cd": "11470"},
    {"name": "성남 분당구", "cd": "41135"},
    {"name": "안양 동안구", "cd": "41173"},
    {"name": "노원구", "cd": "11350"},
]

print("\n=== [현행 로직] 주요 학권지 학원 밀집도 및 점수 ===\n")
print(f"{'지역명':<10} | {'학원수':<6} | {'인구':<10} | {'1,000명당':<10} | {'학원점수'}")
print("-" * 65)

for s in samples:
    pop, comp = fetch_data(token, s['cd'])
    if pop > 0:
        density = comp / (pop / 1000)
        # 현재 코드: min(round((density / 3.0) * 100), 100)
        score = min(round((density / 3.0) * 100), 100)
        print(f"{s['name']:<10} | {comp:<7} | {pop:<10} | {density:<12.2f} | {score:>5}점")
    else:
        print(f"{s['name']:<10} | 데이터 로드 실패")

print("\n* 만점 기준: 인구 1,000명당 학원 3.0개 이상 (현재 적용 값)")
