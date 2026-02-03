import json
import requests
import time

# 1. 원본 파일 로드
input_file = "../data/combined_news_list.json"
output_file = "../data/bigkinds_detailed_result.json"

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        source_data = json.load(f)
except FileNotFoundError:
    print(f"파일을 찾을 수 없습니다: {input_file}")
    source_data = []

# 2. 헤더 설정
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Referer": "https://www.bigkinds.or.kr/v2/news/search.do"
}

# 3. 새로운 리스트 생성 (기존 리스트를 수정하지 않고 새 리스트에 담음)
new_detailed_list = []

for item in source_data:
    doc_id = item.get("NEWS_ID")
    if not doc_id:
        continue

    # 상세 조회를 위한 파라미터 구성
    params = {
        "docId": doc_id,
        "returnCnt": 1,
        "sectionDiv": 1000
    }

    url = "https://www.bigkinds.or.kr/news/detailView.do"

    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)

        if res.status_code == 200:
            detail_json = res.json()
            # 서버 응답에서 실제 데이터가 들어있는 "detail" 키 추출
            detail_content = detail_json.get("detail", {})

            # 5개 기본 필드 + 새로 가져온 상세 데이터(DETAIL)를 합친 새 딕셔너리 생성
            updated_item = {
                "NEWS_ID": item.get("NEWS_ID"),
                "PROVIDER_LINK_PAGE": item.get("PROVIDER_LINK_PAGE"),
                "TITLE": item.get("TITLE"),
              #  "CONTENT": item.get("CONTENT"),
                "DATE": item.get("DATE"),
                "DETAIL": detail_content.get("CONTENT") # 새로 가져온 상세 정보 통째로 넣기
            }
            new_detailed_list.append(updated_item)
            print(f"매칭 완료: {doc_id}")
        else:
            print(f"응답 오류 ({res.status_code}): {doc_id}")

    except Exception as e:
        print(f"요청 중 에러 ({doc_id}): {e}")

    # 과부하 방지
    time.sleep(0.3)
    # break

# 4. 새로운 파일로 저장 (덮어쓰기가 아닌 새 파일 생성)
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(new_detailed_list, f, ensure_ascii=False, indent=4)

print(f"\n작업 완료! 새 파일 '{output_file}'에 총 {len(new_detailed_list)}건이 저장되었습니다.")