import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def verify_21_json():
    # apiType 21 = 교과별 학업성취 사항 (고등학교)
    url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType=21&pbanYr=2023&schulKndCode=04&sidoCode=11&sggCode=11680"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            res = data.get("list", [])
            with open('test_21_output.json', 'w', encoding='utf-8') as f:
                json.dump(res[:50], f, ensure_ascii=False, indent=2)
            print(f"Saved {len(res)} records to test_21_output.json")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    verify_21_json()
