import google.generativeai as genai
import os

# 예전에 사용된 키를 참조합니다 (주식추천 시스템 폴더에 있던 키)
api_key = "AIzaSyC5n_TojKGzffR7_tArqB6z0LKZ9g4L_Zg"

genai.configure(api_key=api_key)

print(f"API Key: {api_key[:10]}...")
print("Gemini API 상태 확인 중...")

try:
    # 모델 리스트를 호출하여 API 키가 유효한지 확인
    models = list(genai.list_models())
    print("API 키가 유효합니다. 사용 가능한 모델:")
    for m in models[:3]:
        print(f" - {m.name}")
    
    # 실제 콘텐츠 생성을 시도하여 쿼터(Quota) 확인
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello, this is a quota check. Reply with 'OK'.")
    print(f"응답 성공: {response.text.strip()}")
    print("\n[상태] 현재 API 호출이 원활하며, 쿼터 제한이 발생하지 않았습니다.")

except Exception as e:
    print(f"\n[오류 발생] {e}")
    if "429" in str(e) or "quota" in str(e).lower():
        print("상태: 할당량(Quota) 초과 또는 크레딧 부족 상태일 수 있습니다.")
    elif "403" in str(e):
        print("상태: API 키 권한 오류 (사용 중지된 키일 수 있음)")
    else:
        print("상태: 일반적인 연결 오류 또는 기타 API 이슈가 발생했습니다.")
