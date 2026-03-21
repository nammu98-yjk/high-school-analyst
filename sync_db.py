import json
import os
import time
import run_server
from run_server import fetch_schoolinfo_students, fetch_schoolinfo_achievement, SGG_MAP

DB_FILE = "schools_db.json"

def sync_all(refresh_achievement_only=False):
    # 캐시 초기화 (이전 -1 값 재사용 방지)
    run_server.school_data_cache.clear()
    print("  [캐시 초기화 완료]")

    # 기존 DB 로드 (achievement_only 모드에서 학생 데이터 보존)
    full_db = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            full_db = json.load(f)

    print(f"=== [DB SYNC] 수도권 학군 데이터 {'내신지수 갱신' if refresh_achievement_only else '전수 수집'} 시작 ===")
    total_count = len(SGG_MAP)
    current = 0

    for sgg_name, sgg_code in SGG_MAP.items():
        current += 1
        print(f"[{current}/{total_count}] {sgg_name} ({sgg_code}) 처리 중...")

        if refresh_achievement_only:
            # 학생 데이터는 기존 값 유지, achievement만 새로 수집
            existing = full_db.get(sgg_code, {})
            students = existing.get("students", [])
        else:
            students = fetch_schoolinfo_students(sgg_code, sgg_name)
            if not students:
                print(f"  [WARN] {sgg_name} 학생 데이터 없음!")

        achievement = fetch_schoolinfo_achievement(sgg_code, sgg_name)

        full_db[sgg_code] = {
            "name": sgg_name,
            "students": students,
            "achievement": achievement,
            "sync_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        time.sleep(0.1)

    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(full_db, f, ensure_ascii=False, indent=2)

    ok_count = sum(1 for v in full_db.values() if v.get("achievement", -1) >= 0)
    print(f"=== [DB SYNC] 완료! 총 {len(full_db)}개 지역 / 내신지수 수집 성공 {ok_count}개 ===")

if __name__ == "__main__":
    # True: achievement(내신지수)만 재수집 (빠름) / False: 전체 재수집
    sync_all(refresh_achievement_only=True)
