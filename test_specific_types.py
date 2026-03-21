import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def test_type(t):
    url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType={t:02d}&pbanYr=2021&schulKndCode=04&sidoCode=11&sggCode=11680"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            res = data.get("list", [])
            if res:
                print(f"API {t}: Found {len(res)} records. Sample: {res[0].keys()}")
                # Print a row with values
                print(f"  Values: {list(res[0].values())[:10]}")
    except: pass

if __name__ == "__main__":
    for i in [3, 4, 16, 25, 26, 30, 31, 32, 33]:
        test_type(i)
