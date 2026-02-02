import os
from typing import List, Dict
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv  # 추가됨

# LangChain & OpenAI 관련
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document

# 1. 환경 설정 (반드시 최상단에서 실행)
load_dotenv()

app = FastAPI()

# 2. 산업군 종목 매핑
INDUSTRY_MAP: Dict[str, List[str]] = {
    "삼성전자": ["SK하이닉스", "한미반도체", "DB하이텍"],
    "에코프로": ["포스코홀딩스", "엘앤에프", "LG에너지솔루션"],
    "현대차": ["기아", "현대모비스", "현대위아"],
    "NAVER": ["카카오", "크래프톤", "엔씨소프트"]
}

# 3. RAG 초기화 (JSON 파일로부터 데이터 로드)
import json

# JSON 파일 경로
json_file_path = "combined_news_list.json"

# JSON 파일 읽기
try:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        news_data = json.load(f)
    
    # 'content' 필드만 추출하여 past_news_data 리스트 생성
    past_news_data = [item['content'] for item in news_data if 'content' in item]
    
    # 데이터가 비어있는 경우 예외 처리
    if not past_news_data:
        raise ValueError("JSON 파일에 유효한 뉴스 데이터가 없습니다.")

except (FileNotFoundError, json.JSONDecodeError) as e:
    # 파일이 없거나 JSON 파싱 오류 시, 기존의 정적 데이터 사용
    print(f"경고: {e}. 기존의 정적 데이터를 사용합니다.")
    past_news_data = [
        "삼성전자, 반도체 수요 급증으로 분기 최대 실적 달성. 주가 급등 사례",
        "미국 연준, 금리 인상 발표로 나스닥 지수 하락 및 기술주 약세",
        "이차전지 섹터 수주 소식에 따른 관련주 동반 상승",
        "테슬라, 자율주행 소프트웨어 결함으로 주가 하락 사례"
    ]

# API 키 확인 절차 (디버깅용)
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY가 .env 파일에 없거나 로드되지 않았습니다.")

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_texts(past_news_data, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# 4. LLM 설정
llm = ChatOpenAI(model="gpt-4o-mini")

# 5. 통신 규격
class NewsRequest(BaseModel):
    stock_name: str
    content: str
    kospi_status: str
    nasdaq_status: str

# 6. 엔드포인트
@app.get("/")
def health_check():
    return {"status": "RAG Server is Running"}

@app.post("/analyze")
async def analyze_news(data: NewsRequest):
    related_stocks = INDUSTRY_MAP.get(data.stock_name, ["해당 산업군 전반"])
    
    # B. RAG 검색 (최신 문법인 invoke 사용 권장)
    docs = retriever.invoke(data.content)
    past_context = "\n".join([doc.page_content for doc in docs])
    
    template = """
    당신은 전문 주식 분석가입니다. 아래 데이터를 종합하여 투자 가이드를 제시하세요.

    [현재 분석 대상]
    - 종목명: {stock_name}
    - 관련 산업군 종목: {related_stocks}
    - 뉴스 내용: {news_content}

    [시장 거시 지표]
    - KOSPI: {kospi}
    - NASDAQ: {nasdaq}

    [참고할 과거 유사 사례 및 추세]
    {past_context}

    위 내용을 바탕으로 해당 뉴스의 종목이 어떤 추세로 갈지 분석하여 
    [매수 / 매도 / 중립] 가이드를 결정하고 그 이유를 3줄 이내로 요약하세요.
    
    반드시 아래 형식을 유지하세요:
    결정: [값]
    이유: 1. ... 2. ...
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({
        "stock_name": data.stock_name,
        "related_stocks": ", ".join(related_stocks),
        "news_content": data.content,
        "kospi": data.kospi_status,
        "nasdaq": data.nasdaq_status,
        "past_context": past_context
    })
    
    return {
        "stock": data.stock_name,
        "decision_report": response.content
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)