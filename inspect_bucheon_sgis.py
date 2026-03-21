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

# Bucheon (31050)
url = f"https://sgisapi.kostat.go.kr/OpenAPI3/addr/stage.json?accessToken={token}&cd=31050"
data = fetch_json(url)
print("--- SGIS Bucheon (31050) Stages ---")
if data.get('result'):
    for item in data['result']:
        print(f"CD: {item['cd']} | Name: {item['addr_name']}")

# Check dongs in one of these (e.g. Sosa)
if data.get('result'):
    sosa_cd = data['result'][0]['cd'] # Usually 31052
    url2 = f"https://sgisapi.kostat.go.kr/OpenAPI3/addr/stage.json?accessToken={token}&cd={sosa_cd}"
    data2 = fetch_json(url2)
    print(f"\n--- SGIS {sosa_cd} Dongs ---")
    if data2.get('result'):
        print(f"Sample Dong: {data2['result'][0]['addr_name']}")
