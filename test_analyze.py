# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

from run_server import analyze_area

# 덕양구 전체 동 분석 시뮬레이션
results = analyze_area('31101', '덕양구', 'district')
print(f"\n=== 덕양구 분석 결과: {len(results)}개 ===")
for r in results[:10]:
    print(f"  - {r['name']}: {r['totalScore']}점 | 학생수:{r['avgStudents']}명 | 점수:{r['scores']}")
