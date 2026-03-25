import json, urllib.request, urllib.parse, ssl, time, os

# SSL context for handling potential verification issues (use with caution)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. API 키 환경변수 분리 (DATA_GO_KR_API_KEY가 없을 경우 하드코딩된 값 사용)
API_KEY = os.environ.get('DATA_GO_KR_API_KEY', 'adcbb74b26d7f4f80ae4068bba6112d4689cccdc5a8d7ee6594717aeeb26409f')
ENDPOINT = "https://api.odcloud.kr/api/15097972/v1/uddi:a7a3e616-d680-42b9-ae74-f2c5d012da36"

# [수정] 제목 및 설명: 현재는 인구 데이터 위주이나 추후 학원수 API 통합 필요
# - 학생인구, 지역별 인구 데이터 수집 및 DB 구축
# - Fields: "13세남자", "13세여자", ...
# - Geofields: "시도명", "시군구명", "읍면동명"

def fetch_all_population():
    all_data = []
    page = 1
    per_page = 1000
    max_retries = 3
    
    while True:
        print(f"Fetching page {page}...")
        url = f"{ENDPOINT}?serviceKey={API_KEY}&page={page}&perPage={per_page}&returnType=JSON"
        
        success = False
        for retry in range(max_retries):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
                with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
                    data = json.loads(r.read().decode('utf-8'))
                    rows = data.get("data", [])
                    if not rows:
                        success = True # End of data
                        break
                    all_data.extend(rows)
                    if len(rows) < per_page:
                        success = True # End of data
                        break
                    page += 1
                    time.sleep(1.0) # Avoid rate limiting
                    success = True
                    break
            except Exception as e:
                print(f"Error on page {page} (Retry {retry+1}/{max_retries}): {e}")
                time.sleep(2)
        
        if not success:
            # [수정] 3회 재시도 후에도 실패할 경우에만 중단하여 데이터 유실 최소화
            print(f"Moving to next page after failure on page {page}...")
            page += 1
            # 만약 전체 중단이 필요하다면 여기서 break
        
        # rows가 비어있거나 per_page보다 작아 데이터가 끝난 경우
        if 'rows' in locals() and (not rows or len(rows) < per_page):
            break
        if page > 100: # Safety break (if total pages known, use exact value)
            break
            
    return all_data

if __name__ == "__main__":
    pop_data = fetch_all_population()
    print(f"Total rows fetched: {len(pop_data)}")
    
    structured_db = {}
    for row in pop_data:
        sido = (row.get("시도명") or "").strip()
        sgg = (row.get("시군구명") or "").strip()
        dong = (row.get("읍면동명") or "").strip()
        
        # [수정] 키 구성 시 빈 값 처리 미흡 해결: join(filter(None, ...)) 사용
        key = " ".join(filter(None, [sido, sgg, dong]))
        
        # [수정] 키 중복 시 덮어쓰기 문제: 경고 출력
        if key in structured_db:
             print(f"⚠️  중복 키 발견: '{key}' (데이터를 덮어씁니다. 행정기관코드: {row.get('행정기관코드')})")
        
        mid_pop = 0
        high_pop = 0
        # [수정] 정수 변환 시 빈 문자열 처리: or 0 추가
        for age in range(13, 16):
            m = int(row.get(f"{age}세남자") or 0)
            f = int(row.get(f"{age}세여자") or 0)
            mid_pop += m + f
        for age in range(16, 19):
            m = int(row.get(f"{age}세남자") or 0)
            f = int(row.get(f"{age}세여자") or 0)
            high_pop += m + f
            
        structured_db[key] = {
            "mid_pop": mid_pop,
            "high_pop": high_pop,
            "total_students": mid_pop + high_pop,
            # [수정] "계" 필드 정수 변환 시 빈 문자열 처리
            "total_pop": int(row.get("계") or 0),
            "sido": sido,
            "sgg": sgg,
            "dong": dong,
            "code": row.get("행정기관코드")
            # [참고] 학원수(academies)는 별도 학원수 수집 API 로직이 필요함
        }
        
    with open('population_db.json', 'w', encoding='utf-8') as f:
        json.dump(structured_db, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(structured_db)} unique entries to population_db.json")
