import sys, urllib.request, re
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')

# 국어, 수학, 영어가 어떤 Cmb_subject 인지 확인
for sub in range(0, 3):
    url = f"https://apt2.me/apt/highGrade.jsp?area=11680&Cmb_year=2024&Cmb_subject={sub}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")
        
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("tbody tr")
        if not rows: rows = soup.find_all("tr")
        
        # 첫 번째 데이터 행의 과목 열을 확인
        for tr in rows[1:2]:
            tds = tr.find_all(["th", "td"])
            if len(tds) > 0:
                col0 = tds[0].get_text(separator="|", strip=True)
                print(f"Cmb_subject={sub} -> 첫 학교 이름 및 과목: {col0}")
                
    except Exception as e:
        print(f"오류: {e}")
