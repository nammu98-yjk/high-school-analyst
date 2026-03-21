import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def discover_api():
    # Test common API types for achievement data
    # Known types: 01-30
    # Trying to find A-E grade distribution and standard deviation
    for t in [4, 7, 8, 12, 13, 14, 15, 16, 21, 22]:
        url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType={t:02d}&pbanYr=2023&schulKndCode=04&sidoCode=11&sggCode=11680"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                res = data.get("list", [])
                if res:
                    print(f"API Type {t:02d}: Success, Count {len(res)}")
                    sample = res[0]
                    # Check for keywords
                    keys = str(sample.keys())
                    if 'STND' in keys or 'DEVI' in keys or 'A_RATIO' in keys or 'A_COUNT' in keys or 'PRCT' in keys:
                        print(f"  !!! Potential Achievement Data in {t:02d} !!!")
                        print(f"  Sample Keys: {sample.keys()}")
                    else:
                        print(f"  Sample Keys: {list(sample.keys())[:5]}...")
        except:
            pass

if __name__ == "__main__":
    discover_api()
