import sys, urllib.request, re
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

# 강남구(11680) 고등학교 학업성취도(highGrade.jsp) 요청
url = "https://apt2.me/apt/highGrade.jsp?area=11680&Cmb_year=2024"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

try:
    with urllib.request.urlopen(req, timeout=10) as r:
        html = r.read().decode("utf-8", errors="ignore")
    
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tbody tr")
    if not rows:
        rows = soup.find_all("tr")

    print(f"✅ 데이터행 발견: 총 {len(rows)}개")

    if rows:
        print("\n=== 헤더(0번째 줄) 추정 ===")
        headers = [td.get_text(separator="|", strip=True) for td in rows[0].find_all(["th", "td"])]
        for i, h in enumerate(headers):
             print(f"  [{i}]: {h}")

        print("\n=== 상위 5개 학교 데이터 샘플 ==")
        for i, tr in enumerate(rows[1:6]):
             tds = tr.find_all(["th", "td"])
             if len(tds) < 3: continue
             
             cols = []
             for td in tds:
                 cols.append(td.get_text(separator="|", strip=True).replace("\n", "").replace("\r", " "))
                 
             print(f"[학교 {i}]")
             for idx, c in enumerate(cols):
                 print(f"  Col {idx}: {c}")
             print("-" * 40)
             
except Exception as e:
    print(f"오류: {e}")
