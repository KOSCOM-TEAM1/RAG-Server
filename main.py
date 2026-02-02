# 0. 가장 먼저 환경 변수 설정 (중요!)
import os
os.environ['LC_ALL'] = 'C.UTF-8'
os.environ['LANG'] = 'C.UTF-8'

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv()

# --- 이제 나머지 라이브러리를 불러옵니다 ---
import json
from typing import List, Dict
from fastapi import FastAPI
from pydantic import BaseModel

# LangChain & OpenAI 관련
import httpx
from openai import OpenAI as OAIClient # 이름 충돌 방지
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document


# 1. FastAPI 앱 생성
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
json_file_path = "bigkinds_detailed_result.json"

# JSON 파일 읽기
try:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        news_data = json.load(f)
    
    # 'DETAIL' 필드만 추출하여 past_news_data 리스트 생성
    past_news_data = [item['DETAIL'] for item in news_data if 'DETAIL' in item and item['DETAIL']]
    
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

# 커스텀 httpx 클라이언트 생성 및 문제의 헤더 제거
_custom_httpx_client = httpx.Client()
_problematic_headers = [
    "x-stainless-os", "x-stainless-arch", "x-stainless-runtime",
    "x-stainless-runtime-version", "x-stainless-lang", "x-stainless-package-version"
]
for header_name in _problematic_headers:
    if header_name in _custom_httpx_client.headers:
        del _custom_httpx_client.headers[header_name]

# 커스텀 httpx 클라이언트를 사용하는 OpenAI 클라이언트 생성
_openai_client_with_custom_httpx = OAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=_custom_httpx_client
)

embeddings = OpenAIEmbeddings(client=_openai_client_with_custom_httpx.embeddings)
index_path = "faiss_index"

# FAISS 인덱스가 로컬에 저장되어 있는지 확인
if os.path.exists(index_path):
    # 1. 인덱스가 존재하면 로드
    print(f"'{index_path}'에서 기존 인덱스를 로드합니다.")
    vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    print("인덱스 로드 완료.")
else:
    # 2. 인덱스가 없으면 새로 생성
    print(f"'{index_path}'를 찾을 수 없습니다. 새로운 인덱스를 생성합니다.")
    
    # JSON 파일 경로
    json_file_path = "bigkinds_detailed_result.json"

    # JSON 파일 읽기
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            news_data = json.load(f)
        
        # 'DETAIL' 필드만 추출하여 past_news_data 리스트 생성 (None 값 필터링)
        past_news_data = [item['DETAIL'] for item in news_data if item.get('DETAIL')]
        
        if not past_news_data:
            raise ValueError("JSON 파일에 유효한 뉴스 데이터가 없습니다.")

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"경고: {e}. 임시 정적 데이터를 사용합니다.")
        past_news_data = [
            "삼성전자, 반도체 수요 급증으로 분기 최대 실적 달성. 주가 급등 사례",
            "미국 연준, 금리 인상 발표로 나스닥 지수 하락 및 기술주 약세",
        ]

    # FAISS 인덱스를 점진적으로 구축
    if past_news_data:
        initial_text = "초기화용 더미 텍스트"
        vectorstore = FAISS.from_texts([initial_text], embeddings)
        
        chunk_size = 100
        for i in range(0, len(past_news_data), chunk_size):
            chunk = past_news_data[i:i + chunk_size]
            vectorstore.add_texts(chunk)
            print(f"인덱싱 진행: {i + len(chunk)} / {len(past_news_data)} 처리 완료")
        
        # 3. 생성된 인덱스를 로컬에 저장
        print(f"새로운 인덱스를 '{index_path}'에 저장합니다.")
        vectorstore.save_local(index_path)
        print("인덱스 저장 완료.")
    else:
        vectorstore = FAISS.from_texts([], embeddings)

retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# 4. LLM 설정
llm = ChatOpenAI(model="gpt-4o-mini", client=_openai_client_with_custom_httpx.chat.completions)

# 5. 통신 규격
class NewsRequest(BaseModel):
    stock_name: str
    content: str
    kospi_status: str
    nasdaq_status: str

# 추가: LLM의 JSON 응답을 파싱하기 위한 Pydantic 모델
class DecisionReport(BaseModel):
    decision: str
    reason: List[str]

# 6. 엔드포인트
@app.get("/")
def health_check():
    return {"status": "RAG Server is Running"}

@app.post("/analyze")
async def analyze_news(data: NewsRequest):
    related_stocks = INDUSTRY_MAP.get(data.stock_name, ["해당 산업군 전반"])
    
    # B. RAG 검색
    docs = retriever.invoke(data.content)
    past_context = "\n".join([doc.page_content for doc in docs])
    
    # C. LLM 체인 구성
    parser = JsonOutputParser(pydantic_object=DecisionReport)
    
    template = """
    당신은 전문 주식 분석가입니다. 아래 데이터를 종합하여 투자 가이드를 제시하세요.

    {format_instructions}

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
    """
    
    prompt = ChatPromptTemplate.from_template(
        template,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    
    # D. 체인 실행
    try:
        decision_report = chain.invoke({
            "stock_name": data.stock_name,
            "related_stocks": ", ".join(related_stocks),
            "news_content": data.content,
            "kospi": data.kospi_status,
            "nasdaq": data.nasdaq_status,
            "past_context": past_context
        })
    except Exception as e:
        # LLM 파싱 실패 또는 다른 오류 발생 시
        print(f"LLM 체인 실행 중 오류 발생: {e}")
        decision_report = {
            "decision": "오류", 
            "reason": ["LLM 응답을 처리하는 중 문제가 발생했습니다.", str(e)]
        }

    return {
        "stock": data.stock_name,
        "decision_report": decision_report
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)