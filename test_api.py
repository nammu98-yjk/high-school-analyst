import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def main():
    # 인천 부평구 (28, 28237)
    url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType=09&pbanYr=2023&schulKndCode=04&sidoCode=28&sggCode=28237"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("Status:", data.get("resultCode"))
            print("Count:", len(data.get("list", [])))
            if data.get("list"):
                print("First item keys:", data.get("list")[0].keys())
                print("First item data:", data.get("list")[0])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
