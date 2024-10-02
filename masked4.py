import re
from datetime import datetime

def extract_viewing_info(text):
    # '관 람 일 시'라는 부분을 찾아서 그 뒤에 있는 정보를 추출
    match = re.search(r"관\s?람\s?일\s?시\s*(\d{4})\.(\d{2})\.(\d{2})\(\s?([가-힣]+)\s?\)\s?(\d{2}:\d{2})", text)
    if match:
        # 각 정보를 추출
        year = match.group(1)
        month = match.group(2)
        day = match.group(3)
        weekday = match.group(4)
        time = match.group(5)
        
        # 요일을 변환
        days_kor = ['월', '화', '수', '목', '금', '토', '일']
        weekday_eng = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_dict = dict(zip(days_kor, weekday_eng))
        
        viewing_info = {
            "관람년도": year,
            "관람월": month,
            "관람일": day,
            "관람요일": weekday_dict.get(weekday, weekday),  # 요일이 한국어로 입력됨
            "관람시간": time
        }
        return viewing_info
    else:
        return None

# 테스트 예시
text = "관 람 일 시 2024.07.06( 토 ) 19:00 2 회"
viewing_info = extract_viewing_info(text)

if viewing_info:
    print(viewing_info)
else:
    print("날짜 정보를 찾을 수 없습니다.")
