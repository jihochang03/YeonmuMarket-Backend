import pytesseract
from PIL import Image
import re

# Tesseract 경로 설정 (필요한 경우)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 이미지 파일 경로
image_path = "C:/Users/hoyah/Downloads/2_link.jpg"  # 실제 이미지 경로

# 이미지 열기
image = Image.open(image_path)

# Tesseract를 사용하여 이미지에서 텍스트 추출 (한글과 영어 인식)
extracted_text = pytesseract.image_to_string(image, lang="kor+eng")

# 추출된 텍스트 출력 (디버깅용)
#print(extracted_text)

# 텍스트를 파일로 저장 (선택사항)
output_path = "C:/Users/hoyah/Downloads/2_link.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(extracted_text)


def extract_viewing_info(text):
    # '관 람 일 시' 부분을 찾아 그 뒤의 날짜와 시간을 추출 (YYYY.MM.DD HH:MM 형식)
    date_time_pattern = r'관 람 일 시\s*(\d{4})\.(\d{2})\.(\d{2})\s*(\d{2}):(\d{2})'
    match = re.search(date_time_pattern, text)

    if not match:
        return "관람 일시 정보를 찾을 수 없습니다."

    # 추출한 값들을 저장
    year, month, day, hour, minute = match.groups()

    # 결과를 딕셔너리로 반환
    result = {
        '관람년도': year,
        '관람월': month,
        '관람일': day,
        '관람시간': {
            '시': hour,
            '분': minute
        }
    }

    return result

# 예매 번호를 추출하는 함수 정의
def extract_ticket_number(text):
    ticket_number_pattern = r'예 매 번 호\s*([A-Za-z0-9]+)'
    match = re.search(ticket_number_pattern, text)

    if not match:
        return "예매 번호를 찾을 수 없습니다."

    ticket_number = match.group(1)[-10:]
    result = f"Y{ticket_number}"
    return result

# 출연진을 추출하는 함수 정의
def extract_cast(text):
    cast_pattern = r'주 요 출 연 진\s*(.*?)\s*티 켓 수 령 방 법'
    match = re.search(cast_pattern, text, re.DOTALL)

    if not match:
        return "출연진 정보를 찾을 수 없습니다."

    cast_lines = match.group(1).splitlines()
    cast_names = []
    for line in cast_lines:
        clean_line = line.strip()
        name_match = re.search(r'[\uAC00-\uD7A3]{1,2}\s*[\uAC00-\uD7A3]{1,2}\s*[\uAC00-\uD7A3]{1,2}$', clean_line)
        if name_match:
            full_name = name_match.group().replace(' ', '')
            last_three_chars = full_name[-3:]
            cast_names.append(last_three_chars)

    return cast_names

# 총 결제 금액을 추출하는 함수 정의
def extract_total_amount(text):
    amount_pattern = r'총 결 제 금 액.*?(\d{1,3}(,\d{3})*)\s*원'
    match = re.search(amount_pattern, text)

    if not match:
        return "총 결제 금액을 찾을 수 없습니다."

    total_amount = match.group(1)
    return total_amount

# 가격 등급을 추출하는 함수 정의
def extract_price_grade(text):

    line_pattern = r'할 인 금 액.*'
    line_match = re.search(line_pattern, text)

    if not line_match:
        return "할 인 금 액 정보를 찾을 수 없습니다."

    # 추출된 줄의 공백을 제거
    cleaned_line = line_match.group(0).replace(' ', '')
    
    # 괄호 안의 내용을 추출
    reason_pattern = r'\(([^)]*)\)'
    reason_match = re.search(reason_pattern, cleaned_line)

    if not reason_match:
        return "할인 이유를 찾을 수 없습니다."

    # 결과 반환 (공백 없이 추출된 괄호 안의 내용)
    return reason_match.group(1)

# 좌석 번호를 추출하는 함수 정의
def extract_seat_number(text):

    seat_pattern = r'좌 석 정 보\s*(.*)/'
    seat_match = re.search(seat_pattern, text)

    if not seat_match:
        return "좌석 정보를 찾을 수 없습니다."

    # 좌석 정보에서 공백을 제거하고 / 앞까지의 내용 추출
    seat_info = seat_match.group(1).replace(' ', '')

    # 결과 반환
    return seat_info

# @ 뒤의 내용을 추출하는 함수 정의
def extract_line_after_at(text):
    
    pattern = r']\s*(.*?)\s*》'
    match = re.search(pattern, text)

    if not match:
        return "해당 구간의 텍스트를 찾을 수 없습니다."

    extracted_text = match.group(1).replace(' ', '')

    return extracted_text

# 예매 상태 확인 함수 정의
def check_reservation_status(text):
    status_pattern = r'예 매 상 태\s*(.*)'
    match = re.search(status_pattern, text)
    
    if not match:
        raise ValueError("예매 상태 정보를 찾을 수 없습니다.")
    
    reservation_status = match.group(1).strip()
    
    
    return reservation_status

# 추출된 정보를 가져와서 처리하는 코드
try:
    reservation_status = check_reservation_status(extracted_text)
    date_info = extract_viewing_info(extracted_text)
    ticket_number = extract_ticket_number(extracted_text)
    total_amount = extract_total_amount(extracted_text)
    price_grade = extract_price_grade(extracted_text)
    seat_number = extract_seat_number(extracted_text)
    place = extract_line_after_at(extracted_text)

    print("관람 일시 정보:", date_info)
    print("예매 번호:", ticket_number)
    print("총 결제 금액:", total_amount, "원")
    print("할인명:", price_grade)
    print("좌석 번호:", seat_number)
    print("극장명:", place)

except ValueError as e:
    print(e)
