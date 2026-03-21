# -*- coding: utf-8 -*-
"""
crawl_apt2_elite.py
─────────────────────────────────────────────────────────────
apt2.me에서 중학교별 특목고/자사고 진학률 데이터를 크롤링하여 
지역(시군구) 단위의 초고해상도 '내신 경쟁강도/엘리트 학군 지표'를 추출합니다.
"""
import sys, json, time, re
import urllib.request, urllib.parse
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')
DB_PATH = "schools_db.json"

def clean_num(text):
    """'19 명' -> 19, '329 / 183 / 146' -> 329 추출"""
    text = text.replace(",", "")
    nums = [int(n) for n in re.findall(r'\d+', text)]
    return nums[0] if nums else 0

def fetch_apt2_data(sgg_code):
    url = f"https://apt2.me/apt/middle.jsp?area={sgg_code}&Cmb_year=2024"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })
    
    try:
         with urllib.request.urlopen(req, timeout=10) as r:
             html = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
         return {"error": str(e)}

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")
    
    total_grads = 0
    total_elite = 0 # 과고 + 외고 + 자사고 + 영재고 (진짜 엘리트 총합)
    total_science = 0
    total_foreign = 0
    total_jasa = 0
    total_gifted = 0
    
    school_count = 0

    for tr in rows:
        tds = tr.find_all(["th", "td"])
        if len(tds) < 3: continue
        
        col0 = [t.strip() for t in tds[0].get_text(separator="|", strip=True).split("|")]
        col1 = [t.strip() for t in tds[1].get_text(separator="|", strip=True).split("|")]
        col2 = [t.strip() for t in tds[2].get_text(separator="|", strip=True).split("|")]
        
        # 헤더나 다른 형식 제거 (최소 데이터 4개/3개 있어야 정상 행)
        if len(col1) < 4 or len(col2) < 2 or "학교명" in col0[0]:
            continue
            
        try:
            sci = clean_num(col1[0])
            forn = clean_num(col1[1])
            jasa = clean_num(col1[2])
            gift = clean_num(col1[3])
            
            grads = clean_num(col2[0])
            
            if grads > 0:
                school_count += 1
                total_grads += grads
                total_science += sci
                total_foreign += forn
                total_jasa += jasa
                total_gifted += gift
                total_elite += (sci + forn + jasa + gift)
        except:
            continue
            
    if school_count > 0:
        return {
            "schools": school_count,
            "graduates": total_grads,
            "elite_total": total_elite,
            "elite_rate": round(total_elite / total_grads * 100, 2),
            "detail": {"sci": total_science, "forn": total_foreign, "jasa": total_jasa, "gift": total_gifted}
        }
    return None

def main():
    try:
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            db = json.load(f)
    except Exception as e:
        print(f"[DB] 로드 실패: {e}")
        return

    print(f"[DB] {len(db)}개 지역 스캔 시작...")
    
    for key, data in db.items():
        # key format is just the sgg code e.g. "11680"
        sgg = key
        region_name = data.get("name", key)
        
        res = fetch_apt2_data(sgg)
        
        if res and "error" not in res:
            data["elite_stats"] = res
            print(f"✅ {region_name}: {res['schools']}개교 | 엘리트 {res['elite_rate']}% ({res['elite_total']}명/졸업 {res['graduates']}명)")
        else:
             print(f"❌ {region_name}: 수집 실패 혹은 정보 없음")
             
        # 서버 부하 방지
        time.sleep(0.5)

    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("\n[DB] 업데이트 완료! 엘리트 진학률 장착 완료.")

if __name__ == "__main__":
    main()
