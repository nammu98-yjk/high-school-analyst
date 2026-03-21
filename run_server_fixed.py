"""
고등학교 어디가? - 신학군지 분석 서버
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

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# === 캐시 관리 ===
CACHE_FILE = os.path.join(DIRECTORY, 'sgis_cache.json')
api_cache = {}
try:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            api_cache = json.load(f)
except Exception as e:
    print(f"[CACHE] 로드 실패: {e}")

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

def fetch_json(url, timeout=30):
    """외부 API JSON 호출"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            content = resp.read()
            try:
                return json.loads(content.decode('utf-8'))
            except UnicodeDecodeError:
                return json.loads(content.decode('cp949'))
    except Exception as e:
        print(f"  [FETCH ERROR] {url[:60]}... => {e}")
        return None

def fetch_text(url):
    """외부 API 텍스트 호출"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            return resp.read().decode('utf-8')
    except Exception as e:
        print(f"[FETCH ERROR] {url[:80]}... => {e}")
        return None

# === SGIS 데이터 수집 함수들 ===

def sgis_stages(cd=''):
    """행정구역 목록 가져오기"""
    cache_key = f"stages_{cd}"
    if cache_key in api_cache: return api_cache[cache_key]
    
    url = f"{SGIS_BASE}/addr/stage.json?accessToken={sgis_token}"
    if cd:
        url += f"&cd={cd}"
    data = fetch_json(url)
    if data and data.get('errCd') == 0:
        api_cache[cache_key] = data['result']
        return data['result']
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
        # 성공적으로 조회된 경우만 캐시
        api_cache[cache_key] = result_val
        
    return result_val

def sgis_house_count(adm_cd, year='2023'):
    """주택 수 조회"""
    cache_key = f"house_{adm_cd}_{year}"
    if cache_key in api_cache: return api_cache[cache_key]

    url = f"{SGIS_BASE}/stats/house.json?accessToken={sgis_token}&adm_cd={adm_cd}&year={year}&low_search=0"
    data = fetch_json(url)
    result_val = 0
    if data and data.get('errCd') == 0 and data['result']:
        val = data['result'][0].get('house_cnt', '0')
        if val != 'N/A': result_val = int(val)
        
    if data and data.get('errCd') == 0:
        api_cache[cache_key] = result_val
    return result_val

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

# === 학교알리미 시군구 코드 매핑 (전국 주요 지역) ===
SGG_MAP = {
    # 서울 (11)
    "종로구": "11110", "중구": "11140", "용산구": "11170", "성동구": "11200", "광진구": "11215", "동대문구": "11230", "중랑구": "11260", "성북구": "11290", "강북구": "11305", "도봉구": "11320", "노원구": "11350", "은평구": "11380", "서대문구": "11410", "마포구": "11440", "양천구": "11470", "강서구": "11500", "구로구": "11530", "금천구": "11545", "영등포구": "11560", "동작구": "11590", "관악구": "11620", "서초구": "11650", "강남구": "11680", "송파구": "11710", "강동구": "11740",
    # 부산 (21 -> SI 26)
    "부산중구": "26110", "부산서구": "26140", "부산동구": "26170", "영도구": "26200", "부산진구": "26230", "동래구": "26260", "부산남구": "26290", "부산북구": "26320", "해운대구": "26350", "사하구": "26380", "금정구": "26410", "부산강서구": "26440", "연제구": "26470", "수영구": "26500", "사상구": "26530", "기장군": "26710",
    # 대구 (22 -> SI 27)
    "대구중구": "27110", "대구동구": "27140", "대구서구": "27170", "대구남구": "27200", "대구북구": "27230", "수성구": "27260", "달서구": "27290", "달성군": "27710", "군위군": "27720",
    # 인천 (23 -> SI 28)
    "인천중구": "28110", "인천동구": "28140", "미추홀구": "28177", "연수구": "28185", "남동구": "28200", "부평구": "28237", "계양구": "28245", "인천서구": "28260", "강화군": "28710", "옹진군": "28720",
    # 광주 (24 -> SI 29)
    "광주동구": "29110", "광주서구": "29140", "광주남구": "29170", "광주북구": "29200", "광산구": "29230",
    # 대전 (25 -> SI 30)
    "대전동구": "30110", "대전중구": "30140", "대전서구": "30170", "유성구": "30200", "대덕구": "30230",
    # 울산 (26 -> SI 31)
    "울산중구": "31110", "울산남구": "31140", "울산동구": "31170", "울산북구": "31200", "울주군": "31710",
    # 세종 (29 -> SI 36)
    "세종특별자치시": "36110", "세종시": "36110",
    # 경기 (31 -> SI 41)
    "수원시": "41110", "장안구": "41111", "권선구": "41113", "팔달구": "41115", "영통구": "41117", "성남시": "41130", "수정구": "41131", "중원구": "41133", "분당구": "41135", "의정부시": "41150", "안양시": "41170", "만안구": "41171", "동안구": "41173", "부천시": "41190", "광명시": "41210", "평택시": "41220", "동두천시": "41250", "안산시": "41270", "상록구": "41271", "단원구": "41273", "고양시": "41280", "덕양구": "41281", "일산동구": "41285", "일산서구": "41287", "과천시": "41290", "구리시": "41310", "남양주시": "41360", "오산시": "41370", "시흥시": "41390", "군포시": "41410", "의왕시": "41430", "하남시": "41450", "용인시": "41460", "처인구": "41461", "기흥구": "41463", "수지구": "41465", "파주시": "41480", "이천시": "41500", "안성시": "41550", "김포시": "41570", "화성시": "41590", "광주시": "41610", "양주시": "41630", "포천시": "41650", "여주시": "41670", "연천군": "41800", "가평군": "41820", "양평군": "41830",
    # 강원 (32 -> SI 42)
    "춘천시": "42110", "원주시": "42130", "강릉시": "42150", "동해시": "42170", "태백시": "42190", "속초시": "42210", "삼척시": "42230", "홍천군": "42720", "횡성군": "42730", "영월군": "42750", "평창군": "42760", "정선군": "42770", "철원군": "42780", "화천군": "42790", "양구군": "42800", "인제군": "42810", "고성군": "42820", "양양군": "42830",
    # 충북 (33 -> SI 43)
    "청주시": "43110", "상당구": "43111", "서원구": "43112", "흥덕구": "43113", "청원구": "43114", "충주시": "43130", "제천시": "43150", "보은군": "43720", "옥천군": "43730", "영동군": "43740", "증평군": "43745", "진천군": "43750", "괴산군": "43760", "음성군": "43770", "단양군": "43800",
    # 충남 (34 -> SI 44)
    "천안시": "44110", "천안동남구": "44131", "천안서북구": "44133", "공주시": "44150", "보령시": "44180", "아산시": "44200", "서산시": "44210", "논산시": "44230", "계룡시": "44250", "당진시": "44270", "금산군": "44710", "부여군": "44760", "서천군": "44770", "청양군": "44790", "홍성군": "44800", "예산군": "44810", "태안군": "44825",
    # 전북 (35 -> SI 45)
    "전주시": "45110", "전주완산구": "45111", "전주덕진구": "45113", "군산시": "45130", "익산시": "45140", "정읍시": "45180", "남원시": "45190", "김제시": "45210", "완주군": "45710", "진안군": "45720", "무주군": "45730", "장수군": "45740", "임실군": "45750", "순창군": "45770", "고창군": "45790", "부안군": "45800",
    # 전남 (36 -> SI 46)
    "목포시": "46110", "여수시": "46130", "순천시": "46150", "나주시": "46170", "광양시": "46180", "담양군": "46710", "곡성군": "46720", "구례군": "46730", "고흥군": "46770", "보성군": "46780", "화순군": "46790", "장�def fetch_schoolinfo_achievement(adm_cd, sgg_name):
    """
    고교별 학업성취도 기반 내신경쟁 지수 산출
    공식: 평균 점수 * (100 - A등급 비율)
    """
    sgg_name = sgg_name.strip()
    si_name_map = {"11":"서울", "21":"부산", "22":"대구", "23":"인천", "24":"광주", "25":"대전", "26":"울산", "29":"세종", "31":"경기", "32":"강원", "33":"충북", "34":"충남", "35":"전북", "36":"전남", "37":"경북", "38":"경남", "39":"제주"}
    si_sido = SGIS_TO_SI_SIDO.get(adm_cd[:2], "11")
    
    # 1. 시도 이름을 붙여서 더 구체적인 매칭 시도 (SGG_MAP 활용)
    full_search_name = si_name_map.get(adm_cd[:2], "") + sgg_name
    sgg_code = SGG_MAP.get(full_search_name) or SGG_MAP.get(sgg_name)
    
    cache_key = f"achievement_v2_{si_sido}_{sgg_name}"
    if cache_key in school_data_cache: return school_data_cache[cache_key]

    for year in ["2023", "2024", "2022"]:
        # apiType 16: 교과별 학업성취 사항
        url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={SCHOOL_API_KEY}&apiType=16&pbanYr={year}&schulKndCode=04&sidoCode={si_sido}&sggCode={sgg_code}"
        data = fetch_json(url)
        if data and data.get("resultCode") == "success":
            items = data.get("list", [])
            temp_dict = {} # {school_nm: [indices]}
            
            for item in items:
                # 1학년 1학기 주요과목(국/영/수) 필터링
                grade = str(item.get("COL_1", ""))
                semester = str(item.get("COL_2", ""))
                subject = str(item.get("COL_3", ""))
                
                if ("1학년" in grade or "1" in grade) and ("1학기" in semester or "1" in semester) and any(s in subject for s in ["국어", "수학", "영어"]):
                    try:
                        avg_score = float(str(item.get("COL_6", "0")).replace(",",""))
                        a_ratio = float(str(item.get("COL_8", "0")).replace(",",""))
                        
                        if avg_score > 0:
                            # 공식 적용: 평균 * (100 - A비율)
                            index_val = avg_score * (100 - a_ratio)
                            snm = item.get("SCHUL_NM")
                            if snm not in temp_dict: temp_dict[snm] = []
                            temp_dict[snm].append(index_val)
                    except: continue
            
            school_indices = []
            for snm, vlist in temp_dict.items():
                school_indices.append(sum(vlist) / len(vlist))
            
            if school_indices:
                avg_index = sum(school_indices) / len(school_indices)
                print(f"  [API] 내신지수 수집 완료: {sgg_name} ({avg_index:.1f})")
                school_data_cache[cache_key] = avg_index
                return avg_index

    # 데이터 수집 실패 시 -1 반환 (페이크 데이터 방지)
    school_data_cache[cache_key] = -1
    return -1
11")
    
    cache_key = f"achievement_{si_sido}_{sgg_name}"
    if cache_key in school_data_cache: return school_data_cache[cache_key]

    # 학업성취도는 보통 1년 주기로 업데이트되므로 여러 해 시도
    for year in ["2023", "2024", "2022"]:
        # apiType 16: 교과별 학업성취 사항
        url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={SCHOOL_API_KEY}&apiType=16&pbanYr={year}&schulKndCode=04&sidoCode={si_sido}&sggCode={sgg_code}"
        data = fetch_json(url)
        if data and data.get("resultCode") == "success":
            items = data.get("list", [])
            school_intensities = []
            
            # 학교별/과목별로 데이터 분산되어 있으므로 집계
            # 가이드: COL_1=학년, COL_2=학기, COL_3=교과, COL_7=표준편차, COL_8=A비율
            temp_dict = {} # {school_nm: [intensities]}
            
            for item in items:
                # 1학년 1학기 주요과목(국/영/수) 필터링
                grade = str(item.get("COL_1", ""))
                semester = str(item.get("COL_2", ""))
                subject = str(item.get("COL_3", ""))
                
                if "1학년" in grade and "1학기" in semester and any(s in subject for s in ["국어", "수학", "영어"]):
                    try:
                        std_dev = float(str(item.get("COL_7", "0")).replace(",",""))
                        a_ratio = float(str(item.get("COL_8", "0")).replace(",",""))
                        
                        if std_dev > 0 and a_ratio > 0:
                            # 공식 적용: 1 / ((A/100) * StdDev)
                            intensity = 1 / ((a_ratio / 100) * std_dev)
                            snm = item.get("SCHUL_NM")
                            if snm not in temp_dict: temp_dict[snm] = []
                            temp_dict[snm].append(intensity)
                    except: continue
            
            # 학교별 과목 평균 강도 계산
            for snm, vlist in temp_dict.items():
                school_intensities.append(sum(vlist) / len(vlist))
            
            if school_intensities:
                avg_intensity = sum(school_intensities) / len(school_intensities)
                print(f"  [API] 성취도 수집 완료: {sgg_name} (평균강도: {avg_intensity:.4f})")
                school_data_cache[cache_key] = avg_intensity
                return avg_intensity

    # 데이터 공백 시 0 반환
    school_data_cache[cache_key] = 0
    return 0

def fetch_schoolinfo_students(adm_cd, sgg_name):
    # (Existing function remains same but I'll ensure I don't break it)
    sgg_name = sgg_name.strip()
    si_name_map = {"11":"서울", "21":"부산", "22":"대구", "23":"인천", "24":"광주", "25":"대전", "26":"울산", "37":"경북", "38":"경남", "35":"전북", "36":"전남", "34":"충남", "33":"충북", "32":"강원", "31":"경기"}
    full_search_name = si_name_map.get(adm_cd[:2], "") + sgg_name
    sgg_code = SGG_MAP.get(full_search_name) or SGG_MAP.get(sgg_name)
    si_sido = SGIS_TO_SI_SIDO.get(adm_cd[:2], "11")
    
    cache_key = f"{si_sido}_{sgg_name}_{adm_cd[:5]}"
    if cache_key in school_data_cache: return school_data_cache[cache_key]
    
    print(f"  [API] 학교알리미 수집 시작: {sgg_name} (sido={si_sido})")
    for year in ["2023", "2024", "2022"]:
        schools = []
        if sgg_code:
            url = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={SCHOOL_API_KEY}&apiType=09&pbanYr={year}&schulKndCode=04&sidoCode={si_sido}&sggCode={sgg_code}"
            data = fetch_json(url)
            if data and data.get("resultCode") == "success":
                items = data.get("list", [])
                for item in items:
                    g1, g2, g3 = safe_int(item.get("COL_S1")), safe_int(item.get("COL_S2")), safe_int(item.get("COL_S3"))
                    if g1+g2+g3 == 0: continue
                    schools.append({"name": str(item.get("SCHUL_NM")), "avg": round((g1 + g2 + g3) / 3)})
        
        if not schools:
            url_sido = f"https://www.schoolinfo.go.kr/openApi.do?apiKey={SCHOOL_API_KEY}&apiType=09&pbanYr={year}&schulKndCode=04&sidoCode={si_sido}"
            data_sido = fetch_json(url_sido)
            if data_sido and data_sido.get("resultCode") == "success":
                for item in data_sido.get("list", []):
                    item_sgg = str(item.get("COL_SGG_NM", "")) or str(item.get("ADRCD_NM", ""))
                    if sgg_name in item_sgg:
                        g1, g2, g3 = safe_int(item.get("COL_S1")), safe_int(item.get("COL_S2")), safe_int(item.get("COL_S3"))
                        if g1+g2+g3 > 0: schools.append({"name": str(item.get("SCHUL_NM")), "avg": round((g1 + g2 + g3) / 3)})
        if schools:
            school_data_cache[cache_key] = schools
            return schools
    return []


# === 분석 로직 ===

def analyze_area(adm_cd, area_name, level='dong'):
    """
    지역 종합 분석
    level: 'city', 'district', 'dong'
    """
    print(f"\n[ANALYZE] {area_name} (adm_cd={adm_cd}, level={level}) 분석 시작...")
    
    if level == 'dong':
        # 동 단위: 직접 데이터 수집
        res = analyze_single_area(adm_cd, area_name, level='dong')
        save_cache()
        return res
    else:
        # 시/구 단위: 하위 동별로 분석 후 리스트 반환
        sub_areas = sgis_stages(adm_cd)
        results = []
        
        # 멀티스레딩으로 속도 극대화 (최대 10개 동을 한 번에 가져옴)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_area = {executor.submit(analyze_single_area, area['cd'], area['addr_name'], level='dong'): area for area in sub_areas}
            for future in concurrent.futures.as_completed(future_to_area):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as exc:
                    print(f"  [ERROR] 멀티스레드 에러: {exc}")
        
        save_cache() # 수집 완료 후 캐시 한 번에 저장
        
        # 정렬 (종합 점수 내림차순)
        results.sort(key=lambda x: x['totalScore'], reverse=True)
        return results

def analyze_single_area(adm_cd, area_name, level='dong'):
    """단일 지역 분석 (집계 기준: 학교/학생수/내신은 상시 구 단위, 학원/아파트는 상황별 해당 단위)"""
    print(f"  [DATA] {area_name} 데이터 수집 중...")
    
    # 0. 구 단위 정보 추출 (광역시/도 단위 경쟁력 분석용)
    district_cd = adm_cd[:5]
    district_name = area_name
    if len(adm_cd) > 5:
        district_list = sgis_stages(adm_cd[:2])
        for d in district_list:
            if d['cd'] == district_cd:
                district_name = d['addr_name']
                break

    # 1. 구 단위 데이터 (상시 구 단위 집계 대상)
    elem_dist = sgis_company_count(district_cd, 'P8512')
    mid_dist = sgis_company_count(district_cd, 'P85211')
    high_dist = sgis_company_count(district_cd, 'P85212') + sgis_company_count(district_cd, 'P8522')
    acad_dist = sgis_company_count(district_cd, 'P855')
    pop_dist = sgis_population(district_cd) or 1
    
    # 2. 로컬 데이터 (학원/아파트: 선택된 단위 기준)
    academy = sgis_company_count(adm_cd, 'P855')
    house = sgis_house_count(adm_cd)
    population = sgis_population(adm_cd) or 1
    
    # 3. 학교알리미 실데이터 (상시 구 단위)
    schools_raw = fetch_schoolinfo_students(adm_cd, district_name)
    avg_students_per_grade = 0
    if schools_raw:
        avg_students_per_grade = round(sum(s['avg'] for s in schools_raw) / len(schools_raw))
    
    # 4. 내신경쟁 지수 산출 (상시 구 단위)
    district_gpa_index = fetch_schoolinfo_achievement(adm_cd, district_name)
    
    # === 점수 산출 및 등급화 ===
    
    # 1. 학교밸런스 (10%): [구단위 집계]
    if high_dist > 0:
        balance_ratio = (elem_dist + mid_dist) / high_dist
    else:
        balance_ratio = elem_dist + mid_dist
    school_balance_score = min(round(balance_ratio * 25), 100)
    
    # 2. 학원밀집 (20%): [선택 단위 집계]
    academy_score = min(round((academy / (population / 1000 + 0.1) / 3) * 100), 100)
    
    # 3. 아파트밀집 (20%): [선택 단위 집계]
    apartment_score = min(round((house / 15000) * 100), 100)
    
    # 4. 고교당 학생수 (25%): [구단위 집계]
    data_source_note = "학교알리미 실데이터"
    if avg_students_per_grade > 0:
        students_score = min(round((avg_students_per_grade / 300) * 100), 100)
    else:
        pop_per_school = pop_dist / (high_dist + 0.1)
        students_score = min(max(100 - round((pop_per_school / 20000) * 50), 0), 100)
        data_source_note = "데이터 공백 (인구 기반 추정치)"
        
    # 5. 내신경쟁 지수 (25%): [구단위 집계 - 요청하신 공식 적용]
    # 지수 = 평균 * (100 - A비율) / 등급제 (S: 5000+, A: 4000+, B: 3000+, C: 나머지)
    if district_gpa_index > 0:
        # 점수 정규화 (최고점 6000 기준 100점)
        gpa_intensity_score = min(round((district_gpa_index / 5500) * 100), 100)
        gpa_grade = 'S' if district_gpa_index >= 5000 else 'A' if district_gpa_index >= 4000 else 'B' if district_gpa_index >= 3000 else 'C'
        intensity_note = f"학교알리미 실데이터 기반 지수: {district_gpa_index:.1f} ({gpa_grade}등급)"
    else:
        gpa_intensity_score = 0
        gpa_grade = 'N/A'
        intensity_note = "학교알리미 실데이터 수집 실패 (API 확인 필요)"
    
    # 종합 점수
    total = round(
        school_balance_score * 0.10 + 
        academy_score * 0.20 + 
        apartment_score * 0.20 + 
        students_score * 0.25 + 
        gpa_intensity_score * 0.25
    )
    
    grade = 'S+' if total >= 95 else 'A' if total >= 80 else 'B' if total >= 65 else 'C'
    
    result = {
        'name': area_name,
        'adm_cd': adm_cd,
        'districtName': district_name,
        'totalScore': total,
        'grade': grade,
        'avgStudents': avg_students_per_grade,
        'gpaIntensity': district_gpa_index,  # 실제 지수값
        'gpaGrade': gpa_grade,               # 내신경쟁 등급
        'raw': {
            'elementary': elem_dist,
            'middle': mid_dist,
            'high': high_dist,
            'academy': academy,
            'house': house,
            'population': population,
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
        }
    }
    
    print(f"  [SCORE] {area_name}: {total}점 ({grade})")
    return result


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
                year = params.get('year', '2023')
                url = f"{SGIS_BASE}/boundary/hadmarea.geojson?accessToken={sgis_token}&year={year}&adm_cd={adm_cd}&low_search=1"
                data = fetch_json(url)
                self.api_response(data)
            elif path == '/api/analyze':
                adm_cd = params.get('adm_cd', '')
                name = params.get('name', '')
                level = params.get('level', 'dong')
                if not adm_cd:
                    self.api_response({'error': 'adm_cd 파라미터 필요'}, 400)
                    return
                result = analyze_area(adm_cd, name, level)
                self.api_response(result)
            elif path == '/api/token-status':
                self.api_response({'hasToken': sgis_token is not None, 'token': sgis_token[:10] + '...' if sgis_token else None})
            else:
                super().do_GET()
        except Exception as e:
            print(f"[ERROR in do_GET] {e}")
            import traceback
            traceback.print_exc()
            try:
                self.send_error(500, "Internal Server Error")
            except:
                pass

    def api_response(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # API 요청만 로그
        if '/api/' in str(args[0]):
            print(f"  [HTTP] {args[0]}")

# === 서버 실행 ===

if __name__ == '__main__':
    print("=" * 60)
    print("  고등학교 어디가? - 신학군지 분석 서버")
    print("=" * 60)
    
    if not get_sgis_token():
        print("[FATAL] SGIS 토큰 발급 실패. 서비스 ID / 보안키를 확인하세요.")
    
    print(f"\n[SERVER] http://localhost:{PORT} 에서 실행 중...")
    print("[INFO] 브라우저가 자동으로 열립니다.\n")
    
    with socketserver.ThreadingTCPServer(("", PORT), ApiHandler) as httpd:
        webbrowser.open(f"http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[SERVER] 종료합니다.")
