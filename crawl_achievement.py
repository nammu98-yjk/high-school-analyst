# -*- coding: utf-8 -*-
"""
crawl_achievement.py
─────────────────────────────────────────────────────────────
학교알리미 '교과별 학업성취 사항' 반자동 크롤러 (v2)

응답 형식: HTML (script 태그 내 values1 배열로 A~E등급 비율)
- values1[0] = A등급 비율 (%)
- 국어/수학/영어 1학년 A등급 비율 평균 → 내신경쟁강도 역산

[사용 순서]
1. 크롬으로 schoolinfo.go.kr 접속
2. 항목별 공시정보 → 학업성취사항 → 교과별 학업성취 사항
3. 아무 학교 선택 → CAPTCHA(6자리) 입력해서 통과
4. F12 → Application → Cookies → JSESSIONID, WMONID 복사
5. 이 파일 상단에 붙여넣기 후 실행
   python crawl_achievement.py
"""

import sys, json, time, re, os
import urllib.request, urllib.parse
sys.stdout.reconfigure(encoding='utf-8')

# ─── ▼ 쿠키 값 입력 ────────────────────────────────────────
JSESSIONID = "Ut6Y72OdqPYKOD2ulijc3btwLl6UfMXVFlmkuV2ZoWYM01lYtgDE0nMWa0B64Gm1.YmFzZV9kb21haW4vbmdzX3NjYTI="
WMONID     = "jWFu3LLBJqA"
# ─── ▲ ───────────────────────────────────────────────────

BASE_URL   = "https://www.schoolinfo.go.kr"
DB_FILE    = "schools_db.json"
OUT_FILE   = "achievement_db.json"
YEAR       = "2023"
HANGMOK    = "44"

REGION_MAP = {
    "강남구":    ("1100000000", "1168000000"),
    "강동구":    ("1100000000", "1174000000"),
    "강북구":    ("1100000000", "1130500000"),
    "강서구":    ("1100000000", "1150000000"),
    "관악구":    ("1100000000", "1162000000"),
    "광진구":    ("1100000000", "1121500000"),
    "구로구":    ("1100000000", "1153000000"),
    "금천구":    ("1100000000", "1154500000"),
    "노원구":    ("1100000000", "1135000000"),
    "도봉구":    ("1100000000", "1132000000"),
    "동대문구":  ("1100000000", "1123000000"),
    "동작구":    ("1100000000", "1159000000"),
    "마포구":    ("1100000000", "1144000000"),
    "서대문구":  ("1100000000", "1141000000"),
    "서초구":    ("1100000000", "1165000000"),
    "성동구":    ("1100000000", "1120000000"),
    "성북구":    ("1100000000", "1129000000"),
    "송파구":    ("1100000000", "1171000000"),
    "양천구":    ("1100000000", "1147000000"),
    "영등포구":  ("1100000000", "1156000000"),
    "용산구":    ("1100000000", "1117000000"),
    "은평구":    ("1100000000", "1138000000"),
    "종로구":    ("1100000000", "1111000000"),
    "중구":      ("1100000000", "1114000000"),
    "중랑구":    ("1100000000", "1126000000"),
    "수원시":    ("4100000000", "4111000000"),
    "성남시":    ("4100000000", "4113000000"),
    "고양시":    ("4100000000", "4128000000"),
    "용인시":    ("4100000000", "4146000000"),
    "부천시":    ("4100000000", "4119000000"),
    "안산시":    ("4100000000", "4137000000"),
    "안양시":    ("4100000000", "4117000000"),
    "남양주시":  ("4100000000", "4136000000"),
    "화성시":    ("4100000000", "4159000000"),
    "평택시":    ("4100000000", "4122000000"),
    "의정부시":  ("4100000000", "4115000000"),
    "시흥시":    ("4100000000", "4138000000"),
    "파주시":    ("4100000000", "4148000000"),
    "광명시":    ("4100000000", "4121000000"),
    "군포시":    ("4100000000", "4141000000"),
    "광주시":    ("4100000000", "4161000000"),
    "김포시":    ("4100000000", "4157000000"),
    "하남시":    ("4100000000", "4158000000"),
    "이천시":    ("4100000000", "4150000000"),
    "구리시":    ("4100000000", "4130000000"),
    "의왕시":    ("4100000000", "4143000000"),
    "과천시":    ("4100000000", "4129000000"),
    "계양구":    ("2800000000", "2824500000"),
    "남동구":    ("2800000000", "2818500000"),
    "부평구":    ("2800000000", "2821300000"),
    "서구":      ("2800000000", "2826000000"),
    "연수구":    ("2800000000", "2815200000"),
    "미추홀구":  ("2800000000", "2814000000"),
}

def headers():
    return {
        "Cookie": f"JSESSIONID={JSESSIONID}; WMONID={WMONID}",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": f"{BASE_URL}/ei/ss/pneiss_a05_s1.do",
        "Accept": "text/html,application/xhtml+xml,*/*",
    }

def post_json(url, params):
    body = urllib.parse.urlencode(params).encode("utf-8")
    req  = urllib.request.Request(url, data=body, headers=headers(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8", errors="ignore"))
    except:
        return {}

def get_html(url):
    req = urllib.request.Request(url, headers=headers(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode("utf-8", errors="ignore")
    except:
        return ""

def get_school_list(sido_cd, sigungu_cd):
    url  = f"{BASE_URL}/ei/ss/pneiss_a05_s0/selectSchoolListLocation.do"
    data = post_json(url, {
        "GS_HANGMOK_CD": HANGMOK,
        "HG_JONGRYU_GB": "04",
        "SIDO_CODE":     sido_cd,
        "SIGUNGU_CODE":  sigungu_cd,
        "PNF_YR":        YEAR,
        "JG_HANGMOK_CD": "15",
    })
    return data.get("schoolList") or data.get("list") or []

def parse_a_ratio(html: str):
    """
    HTML 내 script에서 A등급 비율(values1[0]) 파싱
    패턴: var values1 = [\n Number('  27.9'||0), ...
    """
    # 모든 values1 블록 추출
    blocks = re.findall(r"var\s+values1\s*=\s*\[(.*?)\]", html, re.DOTALL)
    ratios = []
    for block in blocks:
        nums = re.findall(r"Number\s*\(\s*'\s*([\d.]+)\s*'\s*\|\|0\)", block)
        if nums:
            try:
                ratios.append(float(nums[0]))  # 첫 번째 = A등급 비율
            except:
                pass
    return ratios

def get_achievement(idf_cd):
    """한 학교의 A등급 비율 평균 반환 (국/영/수 1학년 전체 평균)"""
    url = (f"{BASE_URL}/ei/pp/Pneipp_b44_s0p.do"
           f"?SHL_IDF_CD={urllib.parse.quote(idf_cd)}"
           f"&JG_YEAR={YEAR}&GS_HANGMOK_CD={HANGMOK}"
           f"&GS_BURYU_CD=JG220&JG_BURYU_CD=JG040"
           f"&JG_HANGMOK_CD=15&JG_GUBUN=1&JG_CHASU=3"
           f"&LOAD_TYPE=single&isCaptcha=N")
    html = get_html(url)

    if "CAPTCHA" in html.upper() or "captcha" in html or "보안문자" in html:
        return None, "captcha_required"
    if "서비스 일시 중단" in html or len(html) < 100:
        return None, "service_down"

    ratios = parse_a_ratio(html)
    if not ratios:
        return None, "no_data"

    avg = round(sum(ratios) / len(ratios), 2)
    return avg, "ok"

def a_ratio_to_score(avg_a_ratio: float) -> int:
    """
    A등급 비율 → 내신경쟁강도 점수
    A비율이 낮을수록 내신 경쟁이 치열 (희소성 높음)
    강남구 A비율 평균 ≈ 28~35% → 점수 높음
    일반 지역 A비율 ≈ 40~55% → 점수 낮음
    정규화 기준: A비율 20% = 100점, 60% = 0점
    """
    score = (60 - avg_a_ratio) / 40 * 100
    return max(0, min(100, round(score)))

def crawl():
    existing_db = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            existing_db = json.load(f)

    achievement_db = {}
    total_regions  = len(REGION_MAP)
    captcha_hit    = False

    for i, (region, (sido, sigungu)) in enumerate(REGION_MAP.items(), 1):
        print(f"\n[{i}/{total_regions}] {region} 학교 목록 조회...")
        schools = get_school_list(sido, sigungu)
        if not schools:
            print(f"  → 학교 없음")
            continue

        print(f"  → {len(schools)}개 학교")
        a_ratios = []

        for s in schools:
            idf_cd = (s.get("SHL_IDF_CD") or s.get("SCHUL_IDF_CD")
                      or s.get("schulIdfCd") or "")
            name   = s.get("SHL_NM") or s.get("SCHUL_NM") or "?"

            if not idf_cd:
                continue

            ratio, status = get_achievement(idf_cd)

            if status == "captcha_required":
                print(f"    ❌ CAPTCHA 재요구 — 세션이 만료됐습니다!")
                print("    → 브라우저에서 CAPTCHA를 다시 풀고 JSESSIONID를 업데이트하세요.")
                captcha_hit = True
                break
            elif status == "ok" and ratio is not None:
                a_ratios.append(ratio)
                score = a_ratio_to_score(ratio)
                print(f"    ✅ {name}: A비율={ratio}% → {score}점")
            else:
                print(f"    ⚠️  {name}: {status}")

            time.sleep(0.4)

        if captcha_hit:
            break

        if a_ratios:
            avg_a    = round(sum(a_ratios) / len(a_ratios), 2)
            score    = a_ratio_to_score(avg_a)
            achievement_db[region] = {
                "avg_a_ratio": avg_a,
                "score": score,
                "school_count": len(a_ratios),
            }
            print(f"  ★ [{region}] 평균 A비율:{avg_a}% → 내신경쟁강도:{score}점")
        else:
            achievement_db[region] = {"avg_a_ratio": -1, "score": -1, "school_count": 0}

    # 저장
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(achievement_db, f, ensure_ascii=False, indent=2)
    print(f"\n✅ {OUT_FILE} 저장 완료 ({len(achievement_db)}개 지역)")

    # schools_db.json 업데이트
    updated = 0
    for entry in existing_db.values():
        name = entry.get("name", "")
        # 지역명 매칭 (부분 포함)
        for region, achv in achievement_db.items():
            if (name == region or region in name or name in region) and achv["score"] >= 0:
                entry["achievement"] = achv["score"]
                entry["achievement_source"] = "crawled_a_ratio"
                entry["avg_a_ratio"] = achv["avg_a_ratio"]
                updated += 1
                break

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_db, f, ensure_ascii=False, indent=2)
    print(f"✅ schools_db.json 업데이트: {updated}개 지역")

if __name__ == "__main__":
    crawl()
