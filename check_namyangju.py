import json
import urllib.request
import ssl

SGIS_CONSUMER_KEY = 'b9f5f345dcd24b989899'
SGIS_CONSUMER_SECRET = 'f35f7ef12a774550be0e'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get_token():
    url = f"https://sgisapi.kostat.go.kr/OpenAPI3/auth/authentication.json?consumer_key={SGIS_CONSUMER_KEY}&consumer_secret={SGIS_CONSUMER_SECRET}"
    with urllib.request.urlopen(url, context=ctx) as r:
        return json.loads(r.read().decode('utf-8'))['result']['accessToken']

token = get_token()

def get_academy(adm_cd):
    url = f"https://sgisapi.kostat.go.kr/OpenAPI3/stats/company.json?accessToken={token}&year=2024&adm_cd={adm_cd}&class_code=P855&low_search=1"
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read().decode('utf-8'))
        if data.get('result'):
            return int(data['result'][0].get('corp_cnt', 0))
        return 0

# Namyangju Byeollae: 31130520, Dasan 1: 31130580
print("별내동 (31130520) P855 with low_search=1:", get_academy('31130520'))
print("다산1동 (31130580) P855 with low_search=1:", get_academy('31130580'))
