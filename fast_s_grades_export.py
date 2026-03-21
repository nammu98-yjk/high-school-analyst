with open("s_grades_out.txt", "w", encoding="utf-8") as f:
    f.write("--- 현재 캐시 기준 예상 S등급 지역 ---\n")
    for t in s_grades:
        f.write(f"{t[1]}: {t[0]}점\n")
