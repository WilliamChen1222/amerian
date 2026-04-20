import streamlit as st
import yfinance as yf

st.set_page_config(page_title="簡約版美股估值系統", layout="wide")
st.title("🎯 美股 EPS & P/E 估值系統")

ticker_symbol = st.sidebar.text_input("輸入美股代號", "NVDA").upper()

if ticker_symbol:
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    
    # 擷取關鍵數據
    name = info.get("shortName", ticker_symbol)
    current_price = info.get("currentPrice", 0)
    fwd_eps = info.get("forwardEps", 0)
    fwd_pe = info.get("forwardPE", 0)
    
    st.subheader(f"📊 {name} ({ticker_symbol})")
    
    if fwd_eps and fwd_pe:
        # 計算由 P/E 推算的價格
        calculated_target = fwd_eps * fwd_pe
        upside = ((calculated_target - current_price) / current_price) * 100
        
        col1, col2, col3 = st.columns(3)
        col1.metric("目前股價", f"${current_price:.2f}")
        col2.metric("預估 EPS (Forward)", f"${fwd_eps:.2f}")
        col3.metric("預估本益比 (Forward)", f"{fwd_pe:.2f}x")
        
        st.divider()
        
        # 顯示結果
        st.write(f"### 💡 估值結論")
        st.write(f"根據分析師預估之 EPS (${fwd_eps:.2f}) 與目前市場給予的 P/E ({fwd_pe:.2f}x)，")
        st.info(f"目前的合理目標價推估為：**${calculated_target:.2f}** (潛在空間: {upside:.2f}%)")
        
    else:
        st.warning("無法取得該標的的預估 EPS 或 P/E 數據（常見於 ETF 或虧損中的公司）。")
        st.metric("目前股價", f"${current_price:.2f}")
