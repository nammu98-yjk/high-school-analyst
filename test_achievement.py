import urllib.request, json, ssl, urllib.parse
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def test_achievement(sido, sgg):
    print(f"Testing Achievement API for Sido:{sido}, SGG:{sgg}...")
    # apiType 16 is '교과별 학업성취 사항'
    # Params: pbanYr, schulKndCode(04), sidoCode, sggCode
    url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType=16&pbanYr=2023&schulKndCode=04&sidoCode={sido}&sggCode={sgg}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get("list", [])
            print(f"  Found {len(results)} achievement records.")
            if results:
                # Group by school and subject
                # Example record: {"SCHUL_NM": "...", "SBJT_NM": "국어", "AVG_SCOR": "...", "STND_DEVI": "...", "A_COUNT": "..."}
                print("  Sample:", results[0])
    except Exception as e:
        print("  Error:", e)

if __name__ == "__main__":
    test_achievement("11", "11680") # 강남구
