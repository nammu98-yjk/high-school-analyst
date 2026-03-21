import json, urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

SGIS_KEY = 'b9f5f345dcd24b989899'
SGIS_SECRET = 'f35f7ef12a774550be0e'
auth_url = f"https://sgisapi.kostat.go.kr/OpenAPI3/auth/authentication.json?consumer_key={SGIS_KEY}&consumer_secret={SGIS_SECRET}"

req = urllib.request.Request(auth_url)
with urllib.request.urlopen(req, context=ctx) as r:
    token = json.loads(r.read().decode('utf-8'))['result']['accessToken']

url = f"https://sgisapi.kostat.go.kr/OpenAPI3/stats/house.json?accessToken={token}&adm_cd=11&year=2022&low_search=1"
req = urllib.request.Request(url)

try:
    with urllib.request.urlopen(req, context=ctx) as r:
        data = json.loads(r.read().decode('utf-8'))
        print("=== 2022 서울시 산하 구별 SGIS 코드 ===")
        print("  | ".join([f"{item['adm_nm']}:{item['adm_cd']}" for item in data['result'][:10]]))
        
        # '강남구' 찾기
        gangnam_cd = [i['adm_cd'] for i in data['result'] if '강남' in i['adm_nm']]
        if gangnam_cd:
            gangnam_cd = gangnam_cd[0]
            print(f"\n=> 강남구 코드는 '{gangnam_cd}' 입니다.")
            
            # 아파트수 및 총주택수 테스트
            # house_type=02 가 아파트인지 확인하기 위해 searchpopulation 호출 등 
            url_apt = f"https://sgisapi.kostat.go.kr/OpenAPI3/stats/house.json?accessToken={token}&adm_cd={gangnam_cd}&year=2022&low_search=0&house_type=02" # house_type=02 아파트
            req_apt = urllib.request.Request(url_apt)
            with urllib.request.urlopen(req_apt, context=ctx) as ra:
                 res_apt = json.loads(ra.read().decode('utf-8'))['result'][0]
                 print(f"강남구 아파트수: {res_apt}")
            
            # 총 주택수
            url_tot = f"https://sgisapi.kostat.go.kr/OpenAPI3/stats/house.json?accessToken={token}&adm_cd={gangnam_cd}&year=2022&low_search=0" 
            req_tot = urllib.request.Request(url_tot)
            with urllib.request.urlopen(req_tot, context=ctx) as rt:
                 res_tot = json.loads(rt.read().decode('utf-8'))['result'][0]
                 print(f"강남구 총주택수: {res_tot}")
except Exception as e:
    print(e)
