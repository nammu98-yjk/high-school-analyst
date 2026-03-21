import json, urllib.request, urllib.parse, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

API_KEY = 'adcbb74b26d7f4f80ae4068bba6112d4689cccdc5a8d7ee6594717aeeb26409f'
ENDPOINT = "https://api.odcloud.kr/api/15097972/v1/uddi:a7a3e616-d680-42b9-ae74-f2c5d012da36"

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
        with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

url = f"{ENDPOINT}?serviceKey={API_KEY}&page=1&perPage=5&returnType=JSON"
data = fetch_json(url)

with open('pop_fields.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Saved to pop_fields.json")
