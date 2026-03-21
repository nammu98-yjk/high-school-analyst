import urllib.request, json, ssl, urllib.parse
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

def discover_codes(area_name):
    # Try searching for a high school in this area
    # Example: "의령군" -> search "의령"
    search_term = area_name.replace("시", "").replace("군", "").replace("구", "").strip()
    try:
        # Search for any SCHOOL in the district
        # apiType=01 results include SGG_CODE indirectly via ADRCD_CD
        url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={API_KEY}&apiType=01&schulNm={urllib.parse.quote(search_term)}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for item in data.get("list", []):
                # Verify school location
                addr = item.get("ADRCD_NM", "")
                if area_name in addr or search_term in addr:
                    # Found! ADRCD_CD is 10 digits, first 5 is SGG_CODE, first 2 is SIDO_CODE
                    code = item.get("ADRCD_CD", "")
                    if code and len(code) >= 5:
                        return code[:2], code[:5]
    except: pass
    return None, None

def main():
    targets = ["의령군", "강릉시", "수성구", "진도군", "부평구"]
    for t in targets:
        sido, sgg = discover_codes(t)
        print(f"{t} => Sido:{sido}, SGG:{sgg}")

if __name__ == "__main__":
    main()
