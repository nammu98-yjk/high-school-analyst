import urllib.request, json, ssl, urllib.parse
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def universal_fetch(target_name):
    print(f"Universal Fetch for {target_name}...")
    try:
        # Step 1: Search for any school containing district name (e.g. "의령")
        search_term = target_name.replace("시", "").replace("군", "").replace("구", "").strip()
        encoded_nm = urllib.parse.quote(search_term)
        url01 = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType=01&schulNm={encoded_nm}"
        req = urllib.request.Request(url01)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            schools = data.get("list", [])
            print(f"  Found {len(schools)} potential schools.")
            
            sido_code = None
            sgg_code = None
            
            for s in schools:
                # Check if school location matches target district
                addr = s.get("ADRCD_NM", "") + s.get("LCTN_NM", "")
                if target_name in addr or search_term in addr:
                    sido_code = s.get("ATPT_OFCDC_ORG_CODE") or s.get("SIDO_CODE")
                    # Wait! apiType=01 usually returns ADRCD_CD (10 digits). 
                    # SGG code is first 5 digits.
                    adrcd = s.get("ADRCD_CD", "")
                    if adrcd and len(adrcd) >= 5:
                        sgg_code = adrcd[:5]
                        # Correct sidoCode for apiType=09 is often the first 2 digits of adrcd
                        sido_code = adrcd[:2]
                        break
            
            if not sido_code or not sgg_code:
                print("  Could not find codes.")
                return 0
                
            print(f"  Codes Found: Sido={sido_code}, SGG={sgg_code}")
            
            # Step 2: Fetch student counts for the extracted SGG
            url09 = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType=09&pbanYr=2023&schulKndCode=04&sidoCode={sido_code}&sggCode={sgg_code}"
            req09 = urllib.request.Request(url09)
            with urllib.request.urlopen(req09, context=ctx, timeout=10) as resp09:
                data09 = json.loads(resp09.read().decode('utf-8'))
                count = len(data09.get("list", []))
                print(f"  Result Count for apiType=09: {count}")
                return count
                
    except Exception as e:
        print("  Error:", e)
        return 0

if __name__ == "__main__":
    universal_fetch("의령군")
    universal_fetch("해운대구")
    universal_fetch("강화군")
