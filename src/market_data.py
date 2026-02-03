import yfinance as yf

def get_market_data():
    """
    Fetches key macroeconomic and market indicators using yfinance.
    """
    
    def get_last_price_and_status(symbol):
        ticker = yf.Ticker(symbol)
        # Fetch last 2 days to calculate change
        hist = ticker.history(period="2d")
        if len(hist) < 2:
            price = hist['Close'].iloc[-1] if not hist.empty else "N/A"
            return f"{price:.2f}" if isinstance(price, (int, float)) else price, "정보 없음"
            
        last_close = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        
        status = "상승" if last_close > prev_close else "하락" if last_close < prev_close else "보합"
        
        return f"{last_close:.2f}", status

    print("Fetching KOSPI...")
    kospi_price, kospi_status = get_last_price_and_status("^KS11")
    print("Fetching NASDAQ...")
    nasdaq_price, nasdaq_status = get_last_price_and_status("^IXIC")
    print("Fetching USD/KRW Exchange Rate...")
    exchange_rate, currency_status = get_last_price_and_status("KRW=X")
    
    # For single value tickers, just get the last price
    print("Fetching US 10Y Bond Yield...")
    us_10y_bond_price, _ = get_last_price_and_status("^TNX")
    print("Fetching VIX...")
    vix_price, _ = get_last_price_and_status("^VIX")
    print("Fetching WTI Oil Price...")
    wti_price, _ = get_last_price_and_status("CL=F")
    print("All data fetched.")

    # For index_trend, we can use the status of the major domestic index
    index_trend = kospi_status

    return {
        "kospi": f"{kospi_price} ({kospi_status})",
        "nasdaq": f"{nasdaq_price} ({nasdaq_status})",
        "index_trend": index_trend,
        "exchange_rate": exchange_rate,
        "currency_status": currency_status,
        "us_10y_bond": f"{us_10y_bond_price}%",
        "bok_rate": "2.50%",  # Hardcoded Bank of Korea base rate as of Jan 2026
        "vix_index": vix_price,
        "wti_oil": wti_price,
    }
