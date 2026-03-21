# -*- coding: utf-8 -*-
"""
crawl_apt2_high.py
apt2.me에서 고등학교별 학업성취도(표준편차, A등급 비율)를 크롤링하여
지역 단위 고등학교 내신 극한 경쟁도(학업성취도 지표)를 장착합니다.
"""
import sys, json, time, re
import urllib.request
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')
DB_PATH = "schools_db.json"

def fetch_apt2_high(sgg_code):
    url = f"https://apt2.me/apt/highGrade.jsp?area={sgg_code}&Cmb_year=2024"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
         with urllib.request.urlopen(req, timeout=10) as r:
             html = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
         return {"error": str(e)}

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")
    
    total_schools = 0
    sum_avg_score = 0.0
    sum_std_dev = 0.0
    sum_a_rate = 0.0
    
    for tr in rows:
        tds = tr.find_all(["th", "td"])
        if len(tds) < 3: continue
        
        # [0]:학교명/주소, [1]:평균|표준편차, [2]:A/B/C/D/E 비율
        col0 = [t.strip() for t in tds[0].get_text(separator="|", strip=True).split("|")]
        col1 = [t.strip() for t in tds[1].get_text(separator="|", strip=True).split("|")]
        col2 = [t.strip() for t in tds[2].get_text(separator="|", strip=True).split("|")]
        
        # 헤더 건너뛰기
        if "학교명" in col0[0] or len(col1) < 2 or len(col2) < 1:
            continue
            
        try:
            # col1[0] = 평균, col1[1] = 표준편차
            avg_score = float(col1[0])
            std_dev = float(col1[1])
            
            # col2[0] = A/B/C 분포 (예: 53.6/29.6/10.0)
            a_rate_str = col2[0].split("/")[0]
            if a_rate_str == "-":
                # A등급 비율이 공시안된경우 (일반고 체육, 자사고 일부 등)
                continue
                
            a_rate = float(a_rate_str)
            
            if avg_score > 0 and std_dev > 0:
                total_schools += 1
                sum_avg_score += avg_score
                sum_std_dev += std_dev
                sum_a_rate += a_rate
                
        except:
             continue
             
    if total_schools > 0:
        return {
            "schools": total_schools,
            "mean_score": round(sum_avg_score / total_schools, 1),
            "mean_std_dev": round(sum_std_dev / total_schools, 2),
            "mean_a_rate": round(sum_a_rate / total_schools, 2)
        }
    return None

def main():
    try:
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            db = json.load(f)
    except Exception as e:
        print(f"[DB] 에러: {e}")
        return

    print(f"[DB] {len(db)}개 지역 고등학교 내신 지표 스캔 시작...")
    
    for sgg, data in db.items():
        region_name = data.get("name", sgg)
        
        res = fetch_apt2_high(sgg)
        
        if res and "error" not in res:
            data["high_gpa"] = res
            print(f"✅ {region_name}: 고교 {res['schools']}곳 평균 | 표준편차 {res['mean_std_dev']} | A등급 {res['mean_a_rate']}%")
        else:
            print(f"❌ {region_name}: 정보 없음")
             
        # 부하 방지
        time.sleep(0.5)

    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
        
    print("\n[DB] 업데이트 완료! 고등학교 성취도/표준편차 지표가 DB에 추가되었습니다.")

if __name__ == "__main__":
    main()
