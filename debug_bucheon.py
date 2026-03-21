import json, urllib.request, urllib.parse, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

SCHOOL_API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

# Bucheon Sosa-gu codes:
# SGIS: 31053 (Old code?) or something starting with 41...
# Standard Districts in SchoolInfo:
# Bucheon-si: 41190
# Sosa-gu: 41194

print("--- Testing Bucheon Sosa-gu (41194) ---")
url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={SCHOOL_API_KEY}&apiType=09&pbanYr=2023&schulKndCode=04&sidoCode=41&sggCode=41194"
data = fetch_json(url)
print(f"41194 Result: {data.get('resultCode')} | Count: {len(data.get('list', [])) if data.get('list') else 0}")

print("\n--- Testing Bucheon-si (41190) ---")
url2 = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={SCHOOL_API_KEY}&apiType=09&pbanYr=2023&schulKndCode=04&sidoCode=41&sggCode=41190"
data2 = fetch_json(url2)
print(f"41190 Result: {data2.get('resultCode')} | Count: {len(data2.get('list', [])) if data2.get('list') else 0}")

# Check individual schools in the list to see their addresses
if data2.get('list'):
    sample = data2['list'][0]
    print(f"Sample School: {sample.get('SCHUL_NM')} | SGG: {sample.get('ADRCD_NM')}")

# Check population DB for Sosa-gu
print("\n--- Checking Population DB ---")
with open('population_db.json', 'r', encoding='utf-8') as f:
    pop_db = json.load(f)

# Find keys containing '부천' and '소사'
sosa_keys = [k for k in pop_db.keys() if '부천' in k and '소사' in k]
print(f"Sosa Keys: {sosa_keys[:5]}")
