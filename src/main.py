import os
from typing import List, Dict
from fastapi import FastAPI
from pydantic import BaseModel

# LangChain & OpenAI 관련
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate

# Refactored imports
from config import settings
from rag_utils.embedding import create_vector_store_from_json
from prompts import RAG_PROMPT_TEMPLATE, NO_RAG_PROMPT_TEMPLATE
from market_data import get_market_data

app = FastAPI()

# 2. 산업군 종목 매핑
INDUSTRY_MAP: Dict[str, List[str]] = {
    "삼성전자": ["SK하이닉스", "한미반도체", "DB하이텍"],
    "에코프로": ["포스코홀딩스", "엘앤에프", "LG에너지솔루션"],
    "현대차": ["기아", "현대모비스", "현대위아"],
    "NAVER": ["카카오", "크래프톤", "엔씨소프트"],
    "엔비디아": ["AMD", "인텔", "마이크로소프트", "퀄컴"]
}

# 3. RAG 초기화 (설정 파일 사용) - 주석 처리
# vectorstore = create_vector_store_from_json(settings.json_file_path)

# 4. LLM 설정 - 주석 처리
# llm = ChatOpenAI(model="gpt-4o-mini")

# 5. 통신 규격
class NewsRequest(BaseModel):
    stock_name: str
    content: str

# 6. 엔드포인트
@app.get("/")
def health_check():
    return {"status": "RAG Server is Running"}



@app.post("/analyze")
async def analyze_news(data: NewsRequest):
    # Endpoint-level initialization
    vectorstore = create_vector_store_from_json(settings.json_file_path)
    llm = ChatOpenAI(model="gpt-4o-mini")

    related_stocks = INDUSTRY_MAP.get(data.stock_name, ["해당 산업군 전반"])
    market_data = get_market_data()
    
    # RAG 검색 시 유사도 점수 포함
    docs_with_scores = vectorstore.similarity_search_with_relevance_scores(
        data.content, k=2
    )
    
    # 컨텍스트와 응답용 데이터 분리
    past_context = "\n".join(
        [f"- {doc.page_content}" for doc, score in docs_with_scores]
    )
    referenced_cases = [
        {"content": doc.page_content, "score": float(round(score, 4))} 
        for doc, score in docs_with_scores
    ]
    
    prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
    chain = prompt | llm
    
    prompt_input = {
        "stock_name": data.stock_name,
        "related_stocks": ", ".join(related_stocks),
        "news_content": data.content,
        "past_context": past_context,
        **market_data,
    }

    response = chain.invoke(prompt_input)
    
    return {
        "stock": data.stock_name,
        "decision_report": response.content,
        "referenced_cases": referenced_cases,
        "market_data_used": market_data,
    }
    
    

@app.post("/analyze/no-rag")
async def analyze_news_no_rag(data: NewsRequest):
    """Analyzes news without using the RAG context."""
    # Endpoint-level initialization
    llm = ChatOpenAI(model="gpt-4o-mini")

    related_stocks = INDUSTRY_MAP.get(data.stock_name, ["해당 산업군 전반"])
    market_data = get_market_data()

    prompt = ChatPromptTemplate.from_template(NO_RAG_PROMPT_TEMPLATE)
    chain = prompt | llm
    
    prompt_input = {
        "stock_name": data.stock_name,
        "related_stocks": ", ".join(related_stocks),
        "news_content": data.content,
        **market_data,
    }

    response = chain.invoke(prompt_input)
    
    return {
        "stock": data.stock_name,
        "decision_report": response.content,
        "referenced_cases": ["순수 LLM의 일반 지식으로만 분석"],  # RAG를 사용하지 않으므로 고정 메시지 반환
        "market_data_used": market_data,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)