# 1. 기본 이미지 설정
FROM python:3.9-slim

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 애플리케이션 코드 복사
COPY . .

# 6. 포트 노출
EXPOSE 8000

# 7. 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
