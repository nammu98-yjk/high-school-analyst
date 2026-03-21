"""
고등학교 어디가? - 신학군지 분석 서버 (UTF-8)
SGIS + 학교알리미 실데이터 수집 및 분석 백엔드
"""
import http.server
import socketserver
import webbrowser
import os
import urllib.request
import urllib.parse
import json
import ssl
import concurrent.futures
import re

PORT = int(os.environ.get("PORT", "8295"))
IS_PROD = "PORT" in os.environ
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# === 캐시 및 DB 관리 ===
CACHE_FILE = os.path.join(DIRECTORY, 'sgis_cache.json')
DB_FILE = os.path.join(DIRECTORY, 'schools_db.json')
POP_DB_FILE = os.path.join(DIRECTORY, 'population_db.json')
api_cache = {}
school_data_cache = {}
SCHOOLS_DB = {}
POPULATION_DB = {}

try:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            api_cache = json.load(f)
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            SCHOOLS_DB = json.load(f)
            print(f"[DB] 학교 DB 로드 완료: {len(SCHOOLS_DB)}개 지역 데이터 확보.")
    if os.path.exists(POP_DB_FILE):
        with open(POP_DB_FILE, 'r', encoding='utf-8') as f:
            POPULATION_DB = json.load(f)
            print(f"[DB] 학령인구 DB 로드 완료: {len(POPULATION_DB)}개 행정동 데이터 확보.")
except Exception as e:
    print(f"[DB/CACHE] 로드 실패: {e}")

def save_cache():
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(api_cache, f, ensure_ascii=False)
    except Exception as e:
        print(f"[CACHE] 저장 실패: {e}")

# === API 설정 ===
SGIS_KEY = 'b9f5f345dcd24b989899'
SGIS_SECRET = 'f35f7ef12a774550be0e'
SGIS_BASE = 'https://sgisapi.kostat.go.kr/OpenAPI3'
SCHOOL_API_KEY = '709cf20f70e64310bc84a0c5d945a9ea'

# SSL 인증서 문제 우회
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# === 토큰 관리 ===
sgis_token = None

def get_sgis_token():
    global sgis_token
    url = f"{SGIS_BASE}/auth/authentication.json?consumer_key={SGIS_KEY}&consumer_secret={SGIS_SECRET}"
    data = fetch_json(url)
    if data and data.get('errCd') == 0:
        sgis_token = data['result']['accessToken']
        print(f"[AUTH] SGIS Token 발급 성공: {sgis_token[:10]}...")
        return True
    print(f"[AUTH] SGIS Token 발급 실패: {data}")
    return False

# === 전역 상태 관리 ===
def fetch_json(url, timeout=30):
    """외부 API JSON 호출"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            content = resp.read()
            try:
                return json.loads(content.decode('utf-8'))
            except UnicodeDecodeError:
                return json.loads(content.decode('cp949'))
    except Exception as e:
        print(f"  [FETCH ERROR] {url[:60]}... => {e}")
        return None

def safe_int(val):
    try:
        if not val or val == 'N/A': return 0
        return int(str(val).replace(',', ''))
    except:
        return 0

# === SGIS 데이터 수집 함수들 ===

def sgis_stages(cd=''):
    """행정구역 목록 가져오기 (토큰 자동 갱신 및 수도권 필터링)"""
    global sgis_token
    if not sgis_token: get_sgis_token()

    # 최상위(시도) 레벨일 때 필터링
    if not cd:
        url = f"{SGIS_BASE}/addr/stage.json?accessToken={sgis_token}"
        data = fetch_json(url)
        if data and data.get('errCd') == 0:
            result = [s for s in data['result'] if s['cd'] in ["11", "23", "31"]]
            return result
        # 토큰 만료 의심 시 재시도
        get_sgis_token()
        return sgis_stages(cd)

    cache_key = f"stages_{cd}"
    if cache_key in api_cache: return api_cache[cache_key]
    
    url = f"{SGIS_BASE}/addr/stage.json?accessToken={sgis_token}&cd={cd}"
    data = fetch_json(url)
    if data and data.get('errCd') == 0:
        api_cache[cache_key] = data['result']
        return data['result']
    elif data and data.get('errCd') == -401: # 토큰 만료
        get_sgis_token()
        return sgis_stages(cd)
    return []

def sgis_company_count(adm_cd, class_code, year='2023'):
    """특정 산업분류 사업체 수 조회"""
    cache_key = f"company_{adm_cd}_{class_code}_{year}"
    if cache_key in api_cache: return api_cache[cache_key]

    url = f"{SGIS_BASE}/stats/company.json?accessToken={sgis_token}&adm_cd={adm_cd}&year={year}&class_code={class_code}&low_search=0"
    data = fetch_json(url)
    
    result_val = 0
    if data and data.get('errCd') == 0 and data['result']:
        res = data['result'][0]
        val = res.get('corp_cnt', '0')
        if val != 'N/A':
            result_val = int(val)
        else:
            worker = res.get('tot_worker', '0')
            if worker != 'N/A' and int(worker) > 0:
                result_val = 1
                
    if result_val > 0 or (data and data.get('errCd') == 0):
        api_cache[cache_key] = result_val
    return result_val

def sgis_house_stats(adm_cd, year='2022'):
    """주택 통계 (총 주택수, 아파트 비중) 조회"""
    cache_key = f"house_stats_{adm_cd}_{year}"
    if cache_key in api_cache: return api_cache[cache_key]

    total = 0
    apt = 0
    
    # 1. 총 주택수
    url_tot = f"{SGIS_BASE}/stats/house.json?accessToken={sgis_token}&adm_cd={adm_cd}&year={year}&low_search=0"
    data_tot = fetch_json(url_tot)
    if data_tot and data_tot.get('errCd') == 0 and data_tot['result']:
        total = safe_int(data_tot['result'][0].get('house_cnt', '0'))
        
    # 2. 아파트수
    url_apt = f"{SGIS_BASE}/stats/house.json?accessToken={sgis_token}&adm_cd={adm_cd}&year={year}&low_search=0&house_type=02"
    data_apt = fetch_json(url_apt)
    if data_apt and data_apt.get('errCd') == 0 and data_apt['result']:
        apt = safe_int(data_apt['result'][0].get('house_cnt', '0'))
        
    ratio = round((apt / total * 100), 1) if total > 0 else 0
    res = {'total': total, 'apt': apt, 'ratio': ratio}
    
    if total > 0:
        api_cache[cache_key] = res
    return res

def sgis_population(adm_cd, year='2023'):
    """인구 통계 조회"""
    cache_key = f"pop_{adm_cd}_{year}"
    if cache_key in api_cache: return api_cache[cache_key]

    url = f"{SGIS_BASE}/stats/population.json?accessToken={sgis_token}&adm_cd={adm_cd}&year={year}&low_search=0"
    data = fetch_json(url)
    result_val = 0
    if data and data.get('errCd') == 0 and data['result']:
        r = data['result'][0]
        pop = r.get('tot_ppltn', '0')
        if pop != 'N/A': result_val = int(pop)
        
    if data and data.get('errCd') == 0:
        api_cache[cache_key] = result_val
    return result_val

# === 학교알리미 데이터 수집 ===

SGIS_TO_SI_SIDO = {
    "11": "11", # 서울 (공통)
    "23": "28", # 인천 (SGIS)
    "28": "28", # 인천 (표준)
    "31": "41", # 경기 (SGIS)
    "41": "41"  # 경기 (표준)
}

SGG_MAP = {
    # [서울 11]
    "종로구": "11110", "중구": "11140", "용산구": "11170", "성동구": "11200", "광진구": "11215", "동대문구": "11230", "중랑구": "11260", "성북구": "11290", "강북구": "11305", "도봉구": "11320", "노원구": "11350", "은평구": "11380", "서대문구": "11410", "마포구": "11440", "양천구": "11470", "강서구": "11500", "구로구": "11530", "금천구": "11545", "영등포구": "11560", "동작구": "11590", "관악구": "11620", "서초구": "11650", "강남구": "11680", "송파구": "11710", "강동구": "11740",
    # [인천 28]
    "미추홀구": "28177", "연수구": "28185", "남동구": "28200", "부평구": "28237", "계양구": "28245", "강화군": "28710", "옹진군": "28720", "서구": "28260", "동구": "28140", "중구": "11140", # 서울 중구와 중복 방지 필요하나 코드 매칭 로직으로 보완
    # [경기 41]
    "장안구": "41111", "권선구": "41113", "팔달구": "41115", "영통구": "41117", "수중구": "41131", "수정구": "41131", "중원구": "41133", "분당구": "41135", "의정부시": "41150", "만안구": "41171", "동안구": "41173", "부천시": "41190", "원미구": "41192", "소사구": "41194", "오정구": "41196", "광명시": "41210", "평택시": "41220", "동두천시": "41250", "상록구": "41271", "단원구": "41273", "덕양구": "41281", "일산동구": "41285", "일산서구": "41287", "과천시": "41290", "구리시": "41310", "남양주시": "41360", "오산시": "41370", "시흥시": "41390", "군포시": "41410", "의왕시": "41430", "하남시": "41450", "처인구": "41461", "기흥구": "41463", "수지구": "41465", "파주시": "41480", "이천시": "41500", "안성시": "41550", "김포시": "41570", "화성시": "41590", "광주시": "41610", "양주시": "41630", "포천시": "41650", "여주시": "41670", "연천군": "41800", "가평군": "41820", "양평군": "41830"
}
# 중복 지역명 보완 매핑 (시도코드 + 이름)
SGG_MAP_ADV = {
    "11중구": "11140", "23중구": "28110", "23동구": "28140", "23서구": "28260",
    "28중구": "28110", "28동구": "28140", "28서구": "28260"
}

def fetch_schoolinfo_codes(adm_cd, sgg_name):
    """ adm_cd와 sgg_name을 이용해 시도/군구 코드 동적 조회 (강력한 폴백 적용) """
    sido_prefix = adm_cd[:2]
    si_sido = SGIS_TO_SI_SIDO.get(sido_prefix)
    if not si_sido: return None, None

    # 1. 맵에서 보완 (시도별 중복 이름 우선 처리 및 하드코딩된 정확한 매핑 사용)
    sgg_clean = sgg_name.split()[-1] # "부천시 소사구" -> "소사구", "수원시 장안구" -> "장안구", "인천 중구" -> "중구"
    adv_key = sido_prefix + sgg_clean 
    sgg_code = SGG_MAP_ADV.get(adv_key) or SGG_MAP.get(sgg_name) or SGG_MAP.get(sgg_clean)
    if sgg_code: return si_sido, sgg_code

    # 2. SGIS adm_cd(5자리) 폴백 (서울/경기/인천 행정코드 거의 일치)
    if len(adm_cd) >= 5:
        return si_sido, adm_cd[:5]
    
    # 3. 동적 검색 (최후의 수단)
    search_term = sgg_name.replace("시", "").replace("군", "").replace("구", "").strip()
    encoded_nm = urllib.parse.quote(search_term)
    url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={SCHOOL_API_KEY}&apiType=01&schulNm={encoded_nm}"
    data = fetch_json(url)
    if data and data.get("resultCode") == "success":
        for s in data.get("list", []):
            adrcd = s.get("ADRCD_CD", "")
            if adrcd and adrcd.startswith(si_sido) and len(adrcd) >= 5:
                return si_sido, adrcd[:5]
    
    return si_sido, adm_cd[:5] # 정 안되면 SGIS 코드라도 반환

def fetch_schoolinfo_achievement(adm_cd, sgg_name):
    """
    내신 경쟁강도 지수 산출 — 초등학교 순유입률(전입-전출) 기반

    [설계 근거]
    - 학업성취도 API(11~15)는 교육부 정책으로 접근 불가
    - '전입 - 전출' = 순유입률: 학군을 위해 이사 오면서도 떠나지 않는 비율
    - 단순 전입률 대신 순유입률을 써야 신도시 과대평가 방지
      * 신도시: 전입 많지만 전출도 발생 → 순유입 희석
      * 강남 등 기성 학군: 전입 많고 전출 극히 적음 → 순유입 높음
    - 실증: 강남구 순유입 +3.98%, 군포시 -1.31% (현실 정합)

    [정규화 기준 — 순유입률 기준]
    - +5% 이상  → 100점 (최상위 학군)
    - +3%~+5%  → 선형 보간
    - 0%~+3%   → 선형 보간
    - 음수(전출>전입) → 0점
    """
    si_sido, sgg_code = fetch_schoolinfo_codes(adm_cd, sgg_name)
    if not sgg_code: return -1

    cache_key = f"mvin_net_v2_{si_sido}_{sgg_code}"
    if cache_key in school_data_cache:
        return school_data_cache[cache_key]

    total_in = 0
    total_out = 0
    total_students = 0

    for year in ["2023", "2022", "2024"]:
        url = (f"https://www.schoolinfo.go.kr/openApi.do"
               f"?apiKey={SCHOOL_API_KEY}&apiType=10&pbanYr={year}"
               f"&schulKndCode=02&sidoCode={si_sido}&sggCode={sgg_code}")
        data = fetch_json(url)
        if data and data.get("resultCode") == "success":
            items = data.get("list", [])
            if items:
                total_in       = sum(i.get("MVIN_SUM",  0) for i in items)
                total_out      = sum(i.get("MVT_SUM",   0) for i in items)
                total_students = sum(i.get("STDNT_SUM", 0) for i in items)
                print(f"  [내신지수] {sgg_name} 초등 전입:{total_in} 전출:{total_out} 총:{total_students} ({year}년)")
                break

    if total_students == 0:
        school_data_cache[cache_key] = -1
        return -1

    # 순유입률 (음수 가능)
    net_ratio = (total_in - total_out) / total_students * 100

    # 정규화: 순유입률 5%를 만점(100점) 기준, 음수는 0점
    normalized = max(0, min(round((net_ratio / 5.0) * 100), 100))

    school_data_cache[cache_key] = normalized
    print(f"  [내신지수] {sgg_name} 순유입률:{net_ratio:.2f}% → {normalized}점")
    return normalized


def fetch_schoolinfo_students(adm_cd, sgg_name):
    """ 학생수 데이터 수집 (v12: 학년별 상세 인원 추출 기능을 포함한 최종 엔진) """
    si_sido, sgg_code = fetch_schoolinfo_codes(adm_cd, sgg_name)
    if not sgg_code: return []
    
    # 캐시 갱신을 위해 v12 키 사용
    cache_key = f"students_v12_{si_sido}_{sgg_code}"
    if cache_key in school_data_cache: return school_data_cache[cache_key]
    
    print(f"  [PRECISION-TARGET] {sgg_name}({sgg_code}) 정밀 수집 시작...")
    
    for knd in ["04", "03"]:
        for year in ["2023", "2024", "2022"]:
            url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={SCHOOL_API_KEY}&apiType=09&pbanYr={year}&schulKndCode={knd}&sidoCode={si_sido}&sggCode={sgg_code}"
            data = fetch_json(url)
            
            if data and data.get("resultCode") == "success":
                items = data.get("list", [])
                schools = []
                for item in items:
                    # 1. 고도화된 학년별 필드 추출
                    # [Case A] 군포/구리 스타일 (COL_S1, COL_S2, COL_S3)
                    g1 = safe_int(item.get("COL_S1") or item.get("COLS1") or 0)
                    g2 = safe_int(item.get("COL_S2") or item.get("COLS2") or 0)
                    g3 = safe_int(item.get("COL_S3") or item.get("COLS3") or 0)
                    
                    # [Case B] 표준 스타일 (COL8+9, COL10+11, COL12+13)
                    if g1+g2+g3 == 0:
                        g1 = safe_int(item.get("COL8") or item.get("COL_8") or 0) + safe_int(item.get("COL9") or item.get("COL_9") or 0)
                        g2 = safe_int(item.get("COL10") or item.get("COL_10") or 0) + safe_int(item.get("COL11") or item.get("COL_11") or 0)
                        g3 = safe_int(item.get("COL12") or item.get("COL_12") or 0) + safe_int(item.get("COL13") or item.get("COL_13") or 0)
                    
                    # [Case C] 총합만 있는 경우 (COL_S_SUM)
                    ssum = safe_int(item.get("COL_S_SUM") or item.get("COL_SUM") or item.get("COL10") or 0)
                    if g1+g2+g3 == 0 and ssum > 0:
                        g1 = g2 = g3 = round(ssum / 3)
                    
                    total = g1 + g2 + g3
                    if total > 0:
                        schools.append({
                            "name": str(item.get("SCHUL_NM")), 
                            "g1": g1, "g2": g2, "g3": g3,
                            "avg": round(total / 3)
                        })
                
                if schools:
                    print(f"    [SUCCESS] {sgg_name} {len(schools)}개교 상세 데이터 확보")
                    school_data_cache[cache_key] = schools
                    return schools

    school_data_cache[cache_key] = []
    return []

# === 분석 로직 ===

def analyze_area(adm_cd, area_name, level='dong'):
    print(f"\n[ANALYZE] {area_name} (adm_cd={adm_cd}, level={level}) 분석 시작...")
    
    if level == 'dong':
        res = analyze_single_area(adm_cd, area_name)
        save_cache()
        return res
    else:
        # [v22] 하위 구역 조회가 잘 안 되는 '구' 단위 대비 (예: 덕양구)
        sub_areas = sgis_stages(adm_cd)
        print(f"  [DEBUG] {area_name} ({adm_cd}) 하위 구역 {len(sub_areas)}개 발견.")
        
        # 하위 구역이 없거나 에러가 나면 해당 지역 자체(덕양구 등) 분석 결과 반환
        if not sub_areas:
            print(f"  [INFO] 하위 동 조회가 되지 않아 {area_name} 자체 분석을 수행합니다.")
            res = analyze_single_area(adm_cd, area_name)
            return [res] if res else []
            
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_area = {executor.submit(analyze_single_area, area['cd'], area['addr_name']): area for area in sub_areas}
            for future in concurrent.futures.as_completed(future_to_area):
                try:
                    res = future.result()
                    if res: results.append(res)
                except Exception as exc:
                    print(f"  [ERROR] 분석 스레드 에러: {exc}")
        
        save_cache()
        results.sort(key=lambda x: x['totalScore'], reverse=True)
        return results if results else [analyze_single_area(adm_cd, area_name)]


def analyze_single_area(adm_cd, area_name):
    # adm_cd는 동 단위(10자리) 또는 구/시 단위(5자리)
    # 구 코드 = 항상 앞 5자리
    district_cd_sgis = adm_cd[:5]
    sido_prefix = adm_cd[:2]
    standard_sido = SGIS_TO_SI_SIDO.get(sido_prefix, sido_prefix)

    # ─── 구(District) 이름 찾기 ─────────────────────────────────
    # 동 단위로 호출될 때도 상위 구 이름을 알아야 DB를 찾을 수 있다
    district_name = area_name  # 기본값 (구 단위 직접 호출 시)
    district_list = sgis_stages(adm_cd[:2])
    for d in district_list:
        if d['cd'] == district_cd_sgis:
            district_name = d['addr_name']  # 예: "덕양구"
            break

    # ─── DB 조회: "구/시 이름"으로 매칭 ──────────────────────────
    # 동 단위 area_name("화정1동")이 아닌 구 이름("덕양구")으로 검색해야 함
    db_entry = None
    search_name = district_name.replace(" ", "")

    for code, entry in SCHOOLS_DB.items():
        if code[:2] == standard_sido:
            db_name = entry.get("name", "").replace(" ", "")
            if search_name == db_name:  # 완전 일치
                db_entry = entry
                break

    if not db_entry:  # 부분 일치
        for code, entry in SCHOOLS_DB.items():
            if code[:2] == standard_sido:
                db_name = entry.get("name", "").replace(" ", "")
                if search_name in db_name or db_name in search_name:
                    db_entry = entry
                    break

    # ─── 1. 인프라 데이터 (SGIS API - SGIS 코드 유지) ────────────
    elem_dist = sgis_company_count(district_cd_sgis, 'P8512')
    mid_dist = sgis_company_count(district_cd_sgis, 'P85211')
    high_dist = sgis_company_count(district_cd_sgis, 'P85212')
    academy = sgis_company_count(adm_cd, 'P855')
    
    # 동 단위 중/고 학교 수 (학원 밀집도 분모로 사용)
    mid_dong  = sgis_company_count(adm_cd, 'P85211')
    high_dong = sgis_company_count(adm_cd, 'P85212')
    
    hs_stats = sgis_house_stats(adm_cd)
    house = hs_stats['total']
    apartment_ratio = hs_stats['ratio']
    population = sgis_population(adm_cd) or 1
    pop_dist = sgis_population(district_cd_sgis) or 1

    # 2. 학군지 실데이터 (검증된 로컬 DB 우선)
    schools_raw = []
    district_gpa_index = 0
    district_high_gpa = {}
    std_dev = 0
    a_rate = 0
    if db_entry:
        schools_raw = db_entry.get("students", [])
        stats = db_entry.get("elite_stats", {})
        district_high_gpa = db_entry.get("high_gpa", {})
        district_gpa_index = stats.get("elite_rate", -1) if stats else -1
        print(f"  [DB-OK] {area_name} -> {db_entry.get('name')} 학생 {len(schools_raw)}개교 / 엘리트 진학률 {district_gpa_index}%")
    else:
        # DB에 없는 경우 API 폴백 (데이터 없을 땐 -1 보류)
        sgg_standard = standard_sido + adm_cd[2:5]
        schools_raw = fetch_schoolinfo_students(sgg_standard, district_name)
        district_gpa_index = -1

    # 구 단위 고등학교 총 학생 수 (고교당 학생수 점수 산출에 사용)
    total_high_students_dist = sum(s['avg'] * 3 for s in schools_raw) if schools_raw else 0
    avg_students = round(sum(s['avg'] for s in schools_raw) / len(schools_raw)) if schools_raw else 0
    
    # ── 동 단위 중/고 학생 수 (학원 밀집도 분모로 사용) ──────────────
    # [Precision Update] 학령인구 DB에서 해당 동의 '진짜' 중고생(13-18세) 수 추출
    sido_nm = {"11": "서울특별시", "23": "인천광역시", "28": "인천광역시", "31": "경기도"}.get(sido_prefix, "경기도")
    
    dong_students = 0
    dong_students_source = "추정치"
    
    # DB 매칭 시도
    search_key = f"{sido_nm} {district_name} {area_name}"
    pop_data = POPULATION_DB.get(search_key)
    
    if not pop_data:
        # 광역시의 경우 구 이름이 겹칠 수 있으므로 정밀 검색
        matches = [k for k in POPULATION_DB.keys() if k.startswith(sido_nm) and k.endswith(area_name) and district_name in k]
        if matches:
            pop_data = POPULATION_DB[matches[0]]
            
    if pop_data:
        dong_students = pop_data.get("total_students", 0)
        dong_students_source = "주민등록인구(13-18세)"
    else:
        # DB에 없을 경우 기존 방식(학교수 기반)으로 폴백
        avg_mid_school_students = 270 * 3
        avg_high_school_students = (avg_students * 3) if avg_students > 0 else (200 * 3)
        dong_students = (mid_dong * avg_mid_school_students) + (high_dong * avg_high_school_students)
        
        # 학교도 없으면 인구 기반 폴백
        if dong_students == 0 and population > 0:
            dong_students = round(population * 0.08)
            dong_students_source = "인구비례 추정(8%)"
        else:
            dong_students_source = "학교수 기반 추정"

    dong_students_fallback = (dong_students_source != "주민등록인구(13-18세)")
    
    # === 점수 산출 ===
    
    # 1. 학교밸런스 (5%)
    denom = high_dist if high_dist > 0 else 0.1
    school_balance_score = min(round(((elem_dist + mid_dist) / denom) * 20), 100)
    
    # 2. 학원밀집 (25%) — 동 단위 (중+고)학생 100명당 학원 수 기준
    # 학생 100명당 학원이 10.0개 이상이면 만점 (전국 최상위권 변별력)
    # 동 단위 학교 데이터 없으면 인구 기준으로 폴백
    if dong_students > 0:
        academy_per_100_students = academy / (dong_students / 100)
        
        # [혁신] 50:50 복합 지표 산출
        # 지표 A: 상대 밀집도 (4.0개 기준) - 50%
        score_relative = min(round((academy_per_100_students / 4.0) * 100), 100)
        
        # 지표 B: 절대 학원 수 (100개 기준) - 50%
        # 동네에 학원이 총 몇 개가 있는지도 학원가 규모를 결정하는 중요한 요소
        score_absolute = min(round((academy / 100) * 100), 100)
        
        academy_score = round(score_relative * 0.5 + score_absolute * 0.5)
        
        academy_note = (f"복합점수: {academy_score}점 (밀도 {score_relative}점 + 규모 {score_absolute}점) | "
                       f"학원 {academy}개 / 학생 100명당 {academy_per_100_students:.2f}개")
    else:
        # 폴백: 인구 1,000명당 5.0개 기준 (인구 기준도 엄격하게 조정)
        academy_ratio = academy / (population / 1000 + 0.1)
        academy_score = min(round((academy_ratio / 5.0) * 100), 100)
        academy_note = f"공공데이터 공백으로 인구 기준 산출 ({academy_ratio:.2f}/1000명)"
    
    # 3. 아파트비중 (15%) — 아파트 비중 점수 (90% 이상시 만점)
    # 40%부터 점수를 부여하되 90% 달성 시 100점 부여
    apartment_score = min(max(round((apartment_ratio - 40) / 50 * 100), 0), 100)
    
    # 4. 고교당 학생수 (25%) — 구 단위 학교 평균으로 산출
    data_source_note = "학교알리미 실데이터"
    if avg_students > 0:
        students_score = min(round((avg_students / 300) * 100), 100)
    else:
        pop_per_school = pop_dist / (high_dist + 0.1)
        students_score = min(max(100 - round((pop_per_school / 20000) * 50), 0), 100)
        data_source_note = "데이터 공백 (인구 기반 추정치)"
        
    # 5. 내신확보 유리도 (20%) — 중학 엘리트 진학률(50%) + 고교 표준편차(50%) 역지수화
    if district_gpa_index >= 0:
        # 지표 A: 중학교 엘리트 진학률 (0%에 가까울수록 내신 유리하여 100점, 12% 이상이면 0점)
        score_a = max(0, min(100, 100 - (district_gpa_index / 12.0) * 100))
        
        # 지표 B: 고등학교 평균 표준편차 (20 이상일수록 내신 유리하여 100점, 12 이하이면 극심하여 0점)
        std_dev = 0
        a_rate = 0
        if district_high_gpa and "error" not in district_high_gpa:
            std_dev = district_high_gpa.get('mean_std_dev', 0)
            a_rate = district_high_gpa.get('mean_a_rate', 0)
            
        if std_dev > 0:
            score_b = max(0, min(100, (std_dev - 12) / 8.0 * 100))
            gpa_intensity_score = round(score_a * 0.5 + score_b * 0.5)
            detail_note = f"[중학] 엘리트 진학 {district_gpa_index}% | [고교] 표준편차 {std_dev} / A등급 {a_rate}%"
        else:
            gpa_intensity_score = round(score_a)
            detail_note = f"[중학] 엘리트 진학 {district_gpa_index}% (고교 데이터 부재)"
            
        # 점수에 따른 라벨링 (점수가 높을수록 내신 따기 쉬운 블루오션)
        if   gpa_intensity_score >= 80: label = 'A (블루오션 / 내신 확보 매우 유리)'
        elif gpa_intensity_score >= 60: label = 'B (내신 확보 유리)'
        elif gpa_intensity_score >= 40: label = 'C (일반 학군)'
        elif gpa_intensity_score >= 20: label = 'D (내신 경쟁 치열)'
        else:                           label = 'E (레드오션 / 내신 경쟁 초극심)'
        
        intensity_note = f"{label} → {detail_note}"
    else:
        gpa_intensity_score = 0
        intensity_note = "데이터 수집 제한 (확인 불가)"
    
    # 종합 점수 (사용자 요청 비중 반영: 25/25/15/30/5)
    total = round(
        school_balance_score * 0.05 +  # 학교밸런스 (5%)
        students_score * 0.25 +        # 고교당 학생수 (25%)
        academy_score * 0.25 +         # 학원밀집도 (25%)
        apartment_score * 0.15 +       # 아파트비중 (15%)
        gpa_intensity_score * 0.30     # 내신확보 유리도 (30%)
    )
    
    # 종합 평점 (90+ S, 80+ A, 나머지는 10점 단위 차등)
    grade = 'S' if total >= 90 else 'A' if total >= 80 else 'B' if total >= 70 else 'C' if total >= 60 else 'D' if total >= 50 else 'E'
    
    return {
        'name': area_name,
        'adm_cd': adm_cd,
        'districtName': district_name,
        'totalScore': total,
        'grade': grade,
        'avgStudents': avg_students,
        'gpaIntensity': round(district_gpa_index, 1) if district_gpa_index > 0 else 0,
        'schoolsRaw': schools_raw,
        'raw': {
            'elementary': elem_dist, 'middle': mid_dist, 'high': high_dist,
            'academy': academy, 'dongStudents': dong_students, 
            'dongStudentsFallback': dong_students_fallback,
            'dongStudentsSource': dong_students_source,
            'house': house, 'apartmentRatio': apartment_ratio, 'population': population,
            'eliteRate': round(district_gpa_index, 1) if district_gpa_index > 0 else 0,
            'highStdDev': std_dev if district_gpa_index >= 0 else 0,
            'highARate': a_rate if district_gpa_index >= 0 else 0,
        },
        'scores': {
            'schoolBalance': school_balance_score,
            'academyDensity': academy_score,
            'apartmentDensity': apartment_score,
            'studentsPerHigh': students_score,
            'gpaIntensity': gpa_intensity_score,
        },
        'notes': {
            'gpaIntensity': intensity_note,
            'studentsPerHigh': f'{data_source_note} 기반 점수.',
            'academyDensity': academy_note,
        }
    }

# === HTTP 서버 ===

class ApiHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            params = dict(urllib.parse.parse_qsl(parsed.query))
            
            if path == '/api/stages':
                self.api_response(sgis_stages(params.get('cd', '')))
            elif path == '/api/boundary':
                adm_cd = params.get('adm_cd', '')
                year = params.get('year', '2024') # 부천시 원미/소사/오정구 등 신규 행정구역 지원
                url = f"{SGIS_BASE}/boundary/hadmarea.geojson?accessToken={sgis_token}&year={year}&adm_cd={adm_cd}&low_search=1"
                boundary_data = fetch_json(url)
                if str(boundary_data.get('errCd')) == '-100':
                    url_fb = f"{SGIS_BASE}/boundary/hadmarea.geojson?accessToken={sgis_token}&year=2023&adm_cd={adm_cd}&low_search=1"
                    boundary_data = fetch_json(url_fb)
                
                self.api_response(boundary_data)
            elif path == '/api/analyze':
                # 분석 로직...
                adm_cd = params.get('adm_cd', '')
                name = params.get('name', '')
                level = params.get('level', 'dong')
                if not adm_cd:
                    self.api_response({'error': 'adm_cd required'}, 400)
                    return
                self.api_response(analyze_area(adm_cd, name, level))
            elif path == '/api/token-status':
                self.api_response({'hasToken': sgis_token is not None, 'token': (sgis_token[:10] + '...') if sgis_token else None})
            else:
                super().do_GET()
        except Exception as e:
            print(f"[ERROR] {e}")
            self.api_response({'error': str(e)}, 500)

    def api_response(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        if '/api/' in str(args[0]):
            print(f"  [HTTP] {args[0]}")

if __name__ == '__main__':
    print("=" * 60)
    print("  고등학교 어디가? - 신학군지 분석 서버 (Fixed)")
    print("=" * 60)
    
    if get_sgis_token():
        with socketserver.ThreadingTCPServer(("", PORT), ApiHandler) as httpd:
            print(f"\n[SERVER] PORT {PORT} 에서 실행 중...")
            if not IS_PROD:
                webbrowser.open(f"http://localhost:{PORT}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n[SERVER] 종료합니다.")
    else:
        print("[FATAL] SGIS 인증 실패.")
