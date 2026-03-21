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

# Gyeonggi (31)
url = f"https://sgisapi.kostat.go.kr/OpenAPI3/addr/stage.json?accessToken={token}&cd=31"
data = fetch_json(url)
print("--- Gyeonggi (31) Stages ---")
if data.get('result'):
    for item in data['result']:
        print(f"CD: {item['cd']} | Name: {item['addr_name']}")
