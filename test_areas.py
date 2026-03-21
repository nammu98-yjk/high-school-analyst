import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def main():
    # Test Area Code API (apiType=11)
    # Most School Info APIs use this for area codes.
    url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType=11"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("Status:", data.get("resultCode"))
            areas = data.get("list", [])
            print("Count:", len(areas))
            if areas:
                print("First 5 areas:", areas[:5])
                # Search for a rural area, e.g. "의령군" (Uiryeong-gun)
                target = "의령군"
                match = [a for a in areas if target in a.get("SGG_NM", "")]
                print(f"Match for {target}:", match)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
