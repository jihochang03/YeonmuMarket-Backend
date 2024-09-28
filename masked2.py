import cv2
from PIL import Image, ImageDraw

# 좌석 크기를 3배로 늘린 사각형을 그리는 함수
def draw_bounding_box(image_path, output_path, seat_color=(128, 0, 128), box_scale=3):
    # 이미지 불러오기
    image = cv2.imread(image_path)
    height, width, _ = image.shape
    
    # 이미지를 RGB로 변환 (OpenCV는 BGR을 사용하므로 변환 필요)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # 좌석 배치도에서 색칠된 좌석(특정 색상)을 찾기 위해 색상 범위 지정
    lower_bound = (seat_color[0] - 10, seat_color[1] - 10, seat_color[2] - 10)
    upper_bound = (seat_color[0] + 10, seat_color[1] + 10, seat_color[2] + 10)

    # 색상 마스크 생성
    mask = cv2.inRange(image_rgb, lower_bound, upper_bound)

    # 마스크를 사용해 좌석 위치 추출
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # PIL로 이미지를 열어서 사각형 그리기 준비
    pil_image = Image.open(image_path)
    draw = ImageDraw.Draw(pil_image)

    # 각 좌석을 감지하고 사각형 그리기
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # 좌석 크기의 3배로 사각형 크기 설정
        box_x1 = max(0, x - w * (box_scale - 1) // 2)
        box_y1 = max(0, y - h * (box_scale - 1) // 2)
        box_x2 = min(width, x + w + w * (box_scale - 1) // 2)
        box_y2 = min(height, y + h + h * (box_scale - 1) // 2)
        
        # 사각형 그리기
        draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline="red", width=3)

    # 결과 저장
    pil_image.save(output_path)
    print(f"Image saved with bounding boxes: {output_path}")

# 메인 함수
if __name__ == "__main__":
    input_image = "C:/Users/hoyah/Downloads/KakaoTalk_20240928_003948072.jpg"  # 입력 파일 경로
    output_image = "C:/Users/hoyah/Downloads//KakaoTalk_20240928_003948072_output.jpg"  # 출력 파일 경로

    # 색칠된 좌석 색상 (여기서는 예시로 보라색 좌석)
    seat_color = (128, 0, 128)  # RGB값으로 색칠된 좌석의 색상 지정
    draw_bounding_box(input_image, output_image, seat_color)
