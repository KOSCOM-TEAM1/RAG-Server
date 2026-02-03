RAG_PROMPT_TEMPLATE = """
당신은 전문 주식 분석가입니다. 아래 데이터를 종합하여 투자 가이드를 제시하세요.

[현재 분석 대상]
- 종목명: {stock_name}
- 관련 산업군 종목: {related_stocks}
- 뉴스 내용: {news_content}

[시장 거시 지표 및 환경]
- 지수: KOSPI {kospi}, NASDAQ {nasdaq} ({index_trend})
- 통화: 원/달러 환율 {exchange_rate} ({currency_status})
- 금리: 미 10년물 국채 금리 {us_10y_bond}, 한국 기준금리 {bok_rate}
- 변동성: VIX 지수 {vix_index}
- 주요 원자재: WTI 유가 {wti_oil}

[참고할 과거 유사 사례 및 추세]
{past_context}

위 내용을 바탕으로 해당 뉴스의 종목이 어떤 추세로 갈지 분석하여 
[매수 / 매도 / 중립] 가이드를 결정하고 그 이유를 3줄 이내로 요약하세요.

반드시 아래 형식을 유지하세요:
결정: [값]
이유: 1. ... 2. ...
"""

NO_RAG_PROMPT_TEMPLATE = """
당신은 전문 주식 분석가입니다. 아래 데이터를 종합하여 투자 가이드를 제시하세요.

[현재 분석 대상]
- 종목명: {stock_name}
- 관련 산업군 종목: {related_stocks}
- 뉴스 내용: {news_content}

[시장 거시 지표 및 환경]
- 지수: KOSPI {kospi}, NASDAQ {nasdaq} ({index_trend})
- 통화: 원/달러 환율 {exchange_rate} ({currency_status})
- 금리: 미 10년물 국채 금리 {us_10y_bond}, 한국 기준금리 {bok_rate}
- 변동성: VIX 지수 {vix_index} 
- 주요 원자재: WTI 유가 {wti_oil}

위 내용을 바탕으로 해당 뉴스의 종목이 어떤 추세로 갈지 분석하여 
[매수 / 매도 / 중립] 가이드를 결정하고 그 이유를 3줄 이내로 요약하세요.

반드시 아래 형식을 유지하세요:
결정: [값]
이유: 1. ... 2. ...
"""
