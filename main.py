import os
from typing import List, Dict
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv  

# LangChain & OpenAI 관련
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate

from rag_utils.embedding import create_vector_store_from_json

# 1. 환경 설정 (반드시 최상단에서 실행)
load_dotenv()

app = FastAPI()

# 2. 산업군 종목 매핑
INDUSTRY_MAP: Dict[str, List[str]] = {
    "삼성전자": ["SK하이닉스", "한미반도체", "DB하이텍"],
    "에코프로": ["포스코홀딩스", "엘앤에프", "LG에너지솔루션"],
    "현대차": ["기아", "현대모비스", "현대위아"],
    "NAVER": ["카카오", "크래프톤", "엔씨소프트"], 
    "엔비디아": ["AMD", "인텔", "마이크로소프트", "퀄컴"]
}

# 3. RAG 초기화
JSON_FILE_PATH = "bigkinds_detailed_result.json"
vectorstore = create_vector_store_from_json(JSON_FILE_PATH)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# API 키 확인 절차 (디버깅용)
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY가 .env 파일에 없거나 로드되지 않았습니다.")

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

    referenced_cases = [doc.page_content for doc in docs]
    
    return {
        "stock": data.stock_name,
        "decision_report": response.content,
        "referenced_cases": referenced_cases
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)