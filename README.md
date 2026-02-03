# RAG 기반 뉴스 분석 API

## 📖 프로젝트 개요

본 프로젝트는 특정 종목과 관련된 최신 뉴스를 입력받아, **RAG(Retrieval-Augmented Generation)** 모델을 통해 투자 가이드를 생성하는 FastAPI 애플리케이션입니다.

### RAG를 사용하는 이유

- 베이스 모델로 사용되는 `gpt-4o-mini`와 같은 대규모 언어 모델(LLM)은 특정 시점까지의 데이터로 사전 학습됩니다. 이로 인해 모델이 학습한 시점 이후의 최신 정보나 특정 도메인에 대한 깊이 있는 정보는 알지 못하는 한계가 있습니다.
- 본 프로젝트는 이 한계를 극복하기 위해 RAG 기술을 사용합니다. `data/bigkinds_detailed_result.json`에 저장된 **최신 뉴스 기사들을 임베딩하여 벡터 데이터베이스를 구축**합니다.
- 사용자의 질문(뉴스 내용)이 들어오면, LLM의 일반 지식에만 의존하는 것이 아니라, 벡터 DB에서 가장 관련성 높은 최신 뉴스(과거 유사 사례)를 검색하여 함께 프롬프트에 포함시킵니다.
- 이를 통해 LLM은 자신이 학습하지 않은 최신 정보를 바탕으로 더 정확하고 시의성 있는 투자 분석을 생성할 수 있습니다.

LLM이 가진 일반적인 지식에 로컬 데이터를 참조하는 능력을 더하여, 더 깊이 있고 맥락에 맞는 분석을 제공하는 것을 목표로 합니다.

## ✨ 주요 기능 (RAG 중심)

- **🤖 AI 뉴스 분석**: 입력된 뉴스의 내용과 거시 경제 지표(KOSPI, NASDAQ)를 종합하여 해당 종목에 미칠 영향을 분석합니다.
- **📚 유사 사례 검색 (RAG)**: RAG의 핵심 기능으로, 분석의 근거를 마련하기 위해 FAISS 벡터 DB에 저장된 과거 유사 뉴스 사례를 검색하여 가져옵니다. 현재 `data/bigkinds_detailed_result.json` 파일의 데이터를 임베딩하여 이 기능을 수행합니다.
- **⚖️ 투자 가이드 제시**: LLM이 현재 뉴스, 시장 상황, 그리고 RAG를 통해 검색된 과거 유사 사례를 종합적으로 판단하여 `[매수/매도/중립]`의 투자 의견과 그 이유를 명확하게 제시합니다.

## 📂 프로젝트 구조

리팩토링을 통해 프로젝트의 확장성과 유지보수성을 향상시켰습니다.

```
/ 
├── data/ 
│   ├── bigkinds_detailed_result.json
│   └── combined_news_list.json
├── scripts/ 
│   └── crawling.py
├── src/ 
│   ├── config.py
│   ├── main.py
│   └── rag_utils/ 
│       ├── embedding.py
│       └── __init__.py
├── .dockerignore
├── .env
├── .gitignore
├── Dockerfile
├── README.md
└── requirements.txt
```

- **`data/`**: AI 모델 학습 및 분석에 사용되는 원본/가공 데이터 저장
- **`scripts/`**: 데이터 수집(크롤링) 등 일회성 스크립트 저장
- **`src/`**: FastAPI 애플리케이션의 핵심 소스 코드
- **`Dockerfile`**: 애플리케이션의 Docker 이미지 빌드 설정
- **`.env`**: API 키 등 민감한 환경 변수 설정

## 🚀 설치 및 실행

### 준비물

- Python 3.8+
- Docker
- OpenAI API Key

### 1. 환경 설정

1.  **`.env` 파일 생성**
    프로젝트 루트에 `.env` 파일을 생성하고 아래 내용을 추가합니다.
    ```
    OPENAI_API_KEY="sk-..."
    JSON_FILE_PATH="data/bigkinds_detailed_result.json"
    ```

2.  **데이터 준비**
    `data/bigkinds_detailed_result.json` 파일이 필요합니다. `scripts/crawling.py`를 실행하여 생성할 수 있으나, 이를 위해서는 `data/combined_news_list.json` 파일이 먼저 준비되어야 합니다.

### 2. Docker를 이용한 실행

1.  **Docker 이미지 빌드**
    ```bash
    docker build -t rag-server .
    ```

2.  **Docker 컨테이너 실행**
    아래 명령어는 로컬의 `data` 디렉터리를 컨테이너 내부의 `/app/data` 경로로 연결(mount)하여, 데이터 파일이 변경되어도 이미지를 다시 빌드할 필요가 없도록 합니다.
    ```bash
    docker run --rm -p 8000:8000 --env-file .env -v "$(pwd)/data":/app/data rag-server
    ```

## 📖 API 사용법

### `/analyze`

- **Method**: `POST`
- **Description**: 뉴스 내용을 분석하여 투자 가이드를 반환합니다.
- **Request Body**:
    ```json
    {
      "stock_name": "삼성전자",
      "content": "삼전 AI 책봇 활용",
      "kospi_status": "4,950 (+0.5%)",
      "nasdaq_status": "66,000 (+4.1%)"
    }
    ```
- **Response Body**:
    ```json
    {
      "stock": "삼성전자",
      "decision_report": "결정: 매수\n이유: 1. ... 2. ...",
      "referenced_cases": [
        "과거 유사 사례 1의 뉴스 내용",
        "과거 유사 사례 2의 뉴스 내용"
      ]
    }
    ```