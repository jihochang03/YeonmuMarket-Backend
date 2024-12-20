# 빌드 단계
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 필수 패키지 설치 (libGL 포함)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc libgl1 libglib2.0-0 tesseract-ocr tesseract-ocr-kor \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/*

# 작업 디렉토리 설정
WORKDIR /code

# requirements.txt 복사 및 설치
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install --user -r /tmp/requirements.txt

# 최종 이미지 단계
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 필수 패키지 설치 (최종 이미지에서도 libGL 포함)
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 tesseract-ocr tesseract-ocr-kor tesseract-ocr-eng \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/*

# 작업 디렉토리 설정
WORKDIR /code

# 빌드 단계에서 설치한 패키지 복사
COPY --from=builder /root/.local /root/.local

# 프로젝트 복사
COPY . /code/

# PATH 설정
ENV PATH=/root/.local/bin:$PATH

# Tesseract 경로 설정
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# 정적 파일 수집
RUN python manage.py collectstatic --noinput

# 포트 노출
EXPOSE 8000

# Gunicorn으로 WSGI 서버 실행
CMD ["gunicorn", "--bind", ":8000", "config.wsgi"]
