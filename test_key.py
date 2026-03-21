import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def test_api_key():
    url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType=01&schulNm=%EA%B0%95%EB%82%A8"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("Status:", data.get("resultCode"))
            print("Count:", len(data.get("list", [])))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_api_key()
