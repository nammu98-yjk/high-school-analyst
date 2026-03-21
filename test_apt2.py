import sys, urllib.request, re
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')

url = "https://apt2.me/apt/middle.jsp?area=11680&Cmb_year=2024"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

with urllib.request.urlopen(req) as r:
    html = r.read().decode("utf-8", errors="ignore")

soup = BeautifulSoup(html, "html.parser")
rows = soup.select("tbody tr")
if not rows: rows = soup.find_all("tr")

print("=== 테이블 헤더(0번째 줄) ===")
headers = [td.get_text(separator="|", strip=True) for td in rows[0].find_all(["th", "td"])]
for i, h in enumerate(headers):
    print(f"  [{i}]: {h}")

print("\n=== 파싱 로직 적용 결과 ===")
for tr in rows[1:6]:
    tds = tr.find_all(["th", "td"])
    if len(tds) < 3: continue
    
    col0 = tds[0].get_text(separator="|", strip=True).split("|")
    col1 = tds[1].get_text(separator="|", strip=True).split("|")
    col2 = tds[2].get_text(separator="|", strip=True).split("|")
    
    name = col0[0].replace("(년도별실적)","").strip()
    
    print(f"[{name}]")
    print(f"  분야별: {col1}")
    print(f"  졸업생/합계/비율: {col2}\n")
