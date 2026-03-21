import json, urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

SGIS_KEY = 'b9f5f345dcd24b989899'
SGIS_SECRET = 'f35f7ef12a774550be0e'

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

auth_url = f"https://sgisapi.kostat.go.kr/OpenAPI3/auth/authentication.json?consumer_key={SGIS_KEY}&consumer_secret={SGIS_SECRET}"
auth_data = fetch_json(auth_url)
token = auth_data['result']['accessToken']

print("--- Testing Bucheon Boundaries (year=2023, 2022) ---")
b_cd = "31192" # Bucheon Sosa
for year in ["2023", "2022", "2021"]:
    url = f"https://sgisapi.kostat.go.kr/OpenAPI3/boundary/hadmarea.geojson?accessToken={token}&year={year}&adm_cd={b_cd}&low_search=1"
    data = fetch_json(url)
    if not "error" in data and data.get('errCd') == 0:
        print(f"Year {year} SUCCESS for {b_cd}, Features: {len(data['features'])}")
    else:
        print(f"Year {year} FAIL for {b_cd}: {data.get('errCd')} - {data.get('errMsg')}")

print("\n--- Testing Incheon Jung-gu (28) ---")
url = f"https://sgisapi.kostat.go.kr/OpenAPI3/addr/stage.json?accessToken={token}&cd=28"
data = fetch_json(url)
if data.get('result'):
    for item in data['result']:
        print(f"CD: {item['cd']} | Name: {item['addr_name']}")

    junggu_cd = [x['cd'] for x in data['result'] if '중구' in x['addr_name']]
    if junggu_cd:
        print(f"Incheon Jung-gu code is {junggu_cd[0]}")
        year="2023"
        url = f"https://sgisapi.kostat.go.kr/OpenAPI3/boundary/hadmarea.geojson?accessToken={token}&year={year}&adm_cd={junggu_cd[0]}&low_search=1"
        data_b = fetch_json(url)
        if not "error" in data_b and data_b.get('errCd') == 0:
            print(f"Year {year} SUCCESS for {junggu_cd[0]}, Features: {len(data_b['features'])}")
        else:
            print(f"Year {year} FAIL for {junggu_cd[0]}: {data_b.get('errCd')}")
