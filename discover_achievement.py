import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def discover_achievement():
    # Loop through common apiTypes to find achievement stats
    for t in range(1, 40):
        url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType={t:02d}&pbanYr=2023&schulKndCode=04&sidoCode=11&sggCode=11680"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                res = data.get("list", [])
                if not res: continue
                
                # Check for subjects like '국어', '수학' and numbers
                found_subject = False
                for row in res[:5]:
                    val_str = str(row.values())
                    if '수학' in val_str or '국어' in val_str:
                        found_subject = True
                        break
                
                if found_subject:
                    print(f"!!! Potential Match: API Type {t:02d} !!!")
                    print(f"  First item: {res[0]}")
        except:
            pass

if __name__ == "__main__":
    discover_achievement()
