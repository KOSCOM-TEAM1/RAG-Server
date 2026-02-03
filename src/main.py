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

app = FastAPI()

# 2. 산업군 종목 매핑
INDUSTRY_MAP: Dict[str, List[str]] = {
    "삼성전자": ["SK하이닉스", "한미반도체", "DB하이텍"],
    "에코프로": ["포스코홀딩스", "엘앤에프", "LG에너지솔루션"],
    "현대차": ["기아", "현대모비스", "현대위아"],
    "NAVER": ["카카오", "크래프톤", "엔씨소프트"],
    "엔비디아": ["AMD", "인텔", "마이크로소프트", "퀄컴"]
}

# 3. RAG 초기화 (설정 파일 사용)
vectorstore = create_vector_store_from_json(settings.json_file_path)
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
    
    prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
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
    
    

@app.post("/analyze/no-rag")
async def analyze_news_no_rag(data: NewsRequest):
    """Analyzes news without using the RAG context."""
    related_stocks = INDUSTRY_MAP.get(data.stock_name, ["해당 산업군 전반"])
    
    prompt = ChatPromptTemplate.from_template(NO_RAG_PROMPT_TEMPLATE)
    chain = prompt | llm
    
    response = chain.invoke({
        "stock_name": data.stock_name,
        "related_stocks": ", ".join(related_stocks),
        "news_content": data.content,
        "kospi": data.kospi_status,
        "nasdaq": data.nasdaq_status,
    })
    
    return {
        "stock": data.stock_name,
        "decision_report": response.content,
        "referenced_cases": []  # RAG를 사용하지 않으므로 빈 리스트 반환
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)