import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def verify_21():
    # apiType 21 = 교역별 학업성취 사항 (고등학교)
    url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType=21&pbanYr=2023&schulKndCode=04&sidoCode=11&sggCode=11680"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            res = data.get("list", [])
            if res:
                print(f"API Type 21: Count {len(res)}")
                for row in res[:10]:
                    # Print school name and the 'COL' values to identify subjects and achievement
                    print(f"School: {row.get('SCHUL_NM')}, Year: {row.get('PBAN_YR')}")
                    print(f"  Col Values: C1:{row.get('COL_1')}, C2:{row.get('COL_2')}, C3:{row.get('COL_3')}, C4:{row.get('COL_4')}, C5:{row.get('COL_5')}, C6:{row.get('COL_6')}, C7:{row.get('COL_7')}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    verify_21()
