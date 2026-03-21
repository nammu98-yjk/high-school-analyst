import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def test(url):
    print(f"Testing URL: {url[:100]}...")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("  Result:", data.get("resultCode"))
            schools = data.get("list", [])
            print("  Count:", len(schools))
            if schools:
                s = schools[0]
                print(f"  Sample: {s.get('SCHUL_NM')} -> G1:{s.get('COL_S1')}, SGG:{s.get('COL_SGG_NM')}, ADRCD:{s.get('ADRCD_CD')}")
            return len(schools)
    except Exception as e:
        print("  Error:", e)
        return 0

if __name__ == "__main__":
    # Test 1: Bupyeong-gu with Code
    test(f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType=09&pbanYr=2023&schulKndCode=04&sidoCode=28&sggCode=28237")
    # Test 2: Bupyeong-gu with Alternative Code 28060 (Old code)
    test(f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType=09&pbanYr=2023&schulKndCode=04&sidoCode=28&sggCode=28060")
    # Test 3: Incheon Entire (Sido 28)
    test(f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType=09&pbanYr=2023&schulKndCode=04&sidoCode=28")
