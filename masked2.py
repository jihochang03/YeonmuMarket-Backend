import cv2
from PIL import Image, ImageDraw
import os

# 좌석의 가로 크기를 4배로 늘린 사각형을 그리는 함수
def draw_bounding_box(image_path, output_path, width_scale=4):
    # 파일 경로가 존재하는지 확인
    if not os.path.exists(image_path):
        print(f"Error: File not found at {image_path}")
        return
    
    # 이미지 불러오기
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image at {image_path}")
        return
    
    height, width, _ = image.shape
    
    # 이미지를 HSV로 변환
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 보라색 범위 설정 (HSV 색상 값: Hue, Saturation, Value)
    lower_purple = (120, 50, 50)  # 보라색 하한값 (Hue 120~140은 보라색)
    upper_purple = (140, 255, 255)  # 보라색 상한값

    # 보라색 범위 내의 색상 마스크 생성
    mask = cv2.inRange(hsv_image, lower_purple, upper_purple)

    # 마스크를 사용해 좌석 위치 추출
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # PIL로 이미지를 열어서 사각형 그리기 준비
    pil_image = Image.open(image_path)
    draw = ImageDraw.Draw(pil_image)

    # 각 좌석을 감지하고 사각형 그리기
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # 가로는 좌석의 4배, 세로는 좌석과 동일
        box_x1 = max(0, x - w * (width_scale - 1) // 2)  # 가로는 좌석의 4배로 확대
        box_y1 = y  # 세로는 좌석과 동일한 위치
        box_x2 = min(width, x + w + w * (width_scale - 1) // 2)  # 가로 4배로 확대
        box_y2 = y + h  # 세로는 좌석과 동일

        # 직사각형 그리기 (내부도 빨간색으로 채움)
        draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline="red", fill="red", width=3)

    # 결과 저장
    pil_image.save(output_path)
    print(f"Image saved with bounding boxes: {output_path}")

# 메인 함수
if __name__ == "__main__":
    input_image = "C:/Users/hoyah/Downloads/seat3.jpg"  # 입력 파일 경로
    output_image = "C:/Users/hoyah/Downloads/seat3_output.jpg"  # 출력 파일 경로

    # 가로는 4배, 세로는 좌석과 동일하게 직사각형 그리기
    draw_bounding_box(input_image, output_image)

# import cv2
# from PIL import Image, ImageDraw
# import os

# # 좌석 크기를 4배로 늘린 사각형을 그리는 함수 (색상 무관)
# def draw_bounding_box(image_path, output_path, width_scale=4):
#     # 파일 경로가 존재하는지 확인
#     if not os.path.exists(image_path):
#         print(f"Error: File not found at {image_path}")
#         return
    
#     # 이미지 불러오기
#     image = cv2.imread(image_path)
#     if image is None:
#         print(f"Error: Could not load image at {image_path}")
#         return
    
#     height, width, _ = image.shape

#     # 이미지를 그레이스케일로 변환 (색상 무관하게 하기 위해)
#     gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#     # 임계값 적용 (Thresholding) - 좌석을 감지하기 위해
#     _, thresh_image = cv2.threshold(gray_image, 200, 255, cv2.THRESH_BINARY_INV)

#     # 좌석의 윤곽선을 찾기
#     contours, _ = cv2.findContours(thresh_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#     # PIL로 이미지를 열어서 사각형 그리기 준비
#     pil_image = Image.open(image_path)
#     draw = ImageDraw.Draw(pil_image)

#     # 각 좌석을 감지하고 사각형 그리기
#     for contour in contours:
#         x, y, w, h = cv2.boundingRect(contour)
        
#         # 작은 크기의 사각형 무시 (잡음 필터링)
#         if w > 5 and h > 5:  # 좌석 크기를 고려하여 너무 작은 객체는 무시
#             # 가로는 좌석의 4배, 세로는 좌석과 동일
#             box_x1 = max(0, x - w * (width_scale - 1) // 2)  # 가로는 좌석의 4배로 확대
#             box_y1 = y  # 세로는 좌석과 동일한 위치
#             box_x2 = min(width, x + w + w * (width_scale - 1) // 2)  # 가로 4배로 확대
#             box_y2 = y + h  # 세로는 좌석과 동일

#             # 직사각형 그리기 (내부도 빨간색으로 채움)
#             draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline="black", fill="black", width=3)

#     # 결과 저장
#     pil_image.save(output_path)
#     print(f"Image saved with bounding boxes: {output_path}")

# # 메인 함수
# if __name__ == "__main__":
#     input_image = "C:/Users/hoyah/Downloads/seat1.jpg"  # 입력 파일 경로
#     output_image = "C:/Users/hoyah/Downloads/seat1_output.jpg"  # 출력 파일 경로

#     # 가로는 4배, 세로는 좌석과 동일하게 직사각형 그리기
#     draw_bounding_box(input_image, output_image)
