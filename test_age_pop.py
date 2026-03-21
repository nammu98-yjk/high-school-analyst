import urllib.request, urllib.parse, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'
ENDPOINT = "https://api.odcloud.kr/api/15097972/v1/uddi:a7a3e616-d680-42b9-ae74-f2c5d012da36"

# serviceKey를 URL에 직접 삽입 (인코딩 안 함 - 일부 API 필요)
url = f"{ENDPOINT}?serviceKey={API_KEY}&page=1&perPage=3&returnType=JSON"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})

print(f"요청 URL: {url[:100]}...")
try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        raw = r.read()
        print(f"HTTP 200 OK - {len(raw)} bytes")
        data = json.loads(raw.decode('utf-8'))
        print(f"totalCount: {data.get('totalCount')}")
        if data.get('data'):
            sample = data['data'][0]
            print("\n== 첫 번째 row 필드 ==")
            for k, v in list(sample.items())[:20]:
                print(f"  '{k}': {v}")
        else:
            print(f"응답: {str(data)[:300]}")
except Exception as e:
    print(f"[기본] Error: {type(e).__name__}: {e}")

# API key URL 인코딩해서 시도
print("\n--- 인코딩된 키로 재시도 ---")
enc_key = urllib.parse.quote(API_KEY, safe='')
url2 = f"{ENDPOINT}?serviceKey={enc_key}&page=1&perPage=3&returnType=JSON"
req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req2, context=ctx, timeout=15) as r:
        raw = r.read()
        print(f"HTTP 200 OK - {len(raw)} bytes")
        data = json.loads(raw.decode('utf-8'))
        print(f"totalCount: {data.get('totalCount')}")
        if data.get('data'):
            print(json.dumps(data['data'][0], ensure_ascii=False)[:400])
except Exception as e:
    print(f"[인코딩] Error: {type(e).__name__}: {e}")
