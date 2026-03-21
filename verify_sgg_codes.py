import json, urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_fetch_schools(sido, sgg_code):
    url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey=709cf20f70e64310bc84a0c5d945a9ea&apiType=09&pbanYr=2023&schulKndCode=04&sidoCode={sido}&sggCode={sgg_code}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            data = json.loads(r.read().decode('utf-8'))
            print(f"Result for {sido}-{sgg_code}: {data.get('resultCode')} | Count: {len(data.get('list', [])) if data.get('list') else 0}")
    except Exception as e:
        print(f"Error {sido}-{sgg_code}:", e)

# Known codes
# Incheon Jung-gu: 28110
test_fetch_schools("28", "28110")
# Bucheon Wonmi-gu: 41192
test_fetch_schools("41", "41192")
# Bucheon Sosa-gu: 41194
test_fetch_schools("41", "41194")
# Bucheon Ojeong-gu: 41196
test_fetch_schools("41", "41196")
# Incheon Dong-gu: 28140?
test_fetch_schools("28", "28140")

