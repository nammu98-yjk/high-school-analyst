import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def discover():
    # We want to find Average Score and A-ratio.
    # Usually it's in a table with subjects.
    for t in [15, 16, 17, 18, 19, 20, 21]:
        url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType={t:02d}&pbanYr=2023&schulKndCode=04&sidoCode=11&sggCode=11680"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                res = data.get('list', [])
                if res:
                    print(f"--- Type {t:02d} (Count: {len(res)}) ---")
                    for i, row in enumerate(res[:3]):
                        print(f"  Row {i}:", row)
                else:
                    print(f"--- Type {t:02d} (No data) ---")
        except Exception as e:
            print(f"Type {t:02d} Error: {e}")

if __name__ == "__main__":
    discover()
