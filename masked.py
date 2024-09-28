import cv2
import pytesseract
from PIL import Image, ImageDraw
import os

# Tesseract 경로 설정 (필요한 경우)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 주어진 좌표 근처에서 특정 텍스트가 있는지 확인하는 함수
def find_nearby_text(data, x, y, w, h, target_text):
    # 주어진 위치 (x, y, w, h) 근처에서 특정 텍스트를 찾음
    for i in range(len(data['text'])):
        # 탐색할 텍스트 좌표
        text_x, text_y, text_w, text_h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        text = data['text'][i]

        # "번" 글자와 같은 높이(또는 근처에 있는 경우)에서 찾고, 텍스트가 존재하는지 확인
        if abs(text_y - y) < 20 and (text_x > x + w and text_x < x + w + 50) and text == target_text:
            return True
    return False

# 이미지에서 "번" 글자를 찾고 그 옆에 "매" 또는 "호" 글자가 있는지 확인 후 사각형을 그리는 함수
def mask_booking_number_in_image(input_image, output_image):
    try:
        # 이미지 파일 열기 (Pillow 사용)
        image = Image.open(input_image)
        draw = ImageDraw.Draw(image)

        # 이미지에서 텍스트를 OCR로 추출 (한글 인식 추가)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang='kor')

        # OCR로 추출된 텍스트에서 "번" 글자 찾기
        n_boxes = len(data['text'])
        found = False
        for i in range(n_boxes):
            if '번' in data['text'][i]:  # '번' 글자를 포함하는 텍스트 찾기
                # 텍스트 위치 좌표 가져오기
                (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])

                # "번" 글자의 오른쪽 근처에 "매" 또는 "호" 글자가 있는지 확인
                if find_nearby_text(data, x, y, w, h, "매") or find_nearby_text(data, x, y, w, h, "호"):
                    found = True
                    # "매" 또는 "호" 글자가 있는 경우 해당 줄에 사각형 그리기
                    image_width = image.width
                    draw.rectangle([(0, y - 10), (image_width, y + h + 10)], fill="black")

        if found:
            # 마스킹된 이미지 저장
            image.save(output_image)
            print(f"Successfully created masked image: {output_image}")
        else:
            print("번, 매 또는 호 글자를 찾지 못했습니다.")

    except Exception as e:
        print(f"An error occurred: {e}")

# 메인 함수
if __name__ == "__main__":
    input_image = "C:/Users/hoyah/Downloads/ticket_image_24.jpg"
    output_image = "C:/Users/hoyah/Downloads/masked_ticket_image_24.png"
    if os.path.exists(input_image):
        mask_booking_number_in_image(input_image, output_image)
    else:
        print(f"Input file does not exist: {input_image}")
