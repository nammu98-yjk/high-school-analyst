import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def check_keys_4():
    url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType=04&pbanYr=2023&schulKndCode=04&sidoCode=11&sggCode=11680"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            res = data.get("list", [])
            if res:
                print(f"Keys in Type 04: {res[0].keys()}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    check_keys_4()
