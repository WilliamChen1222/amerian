import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 設定網頁標題與寬度
st.set_page_config(page_title="美股目標價分析系統", layout="wide")
st.title("📈 美股目標股價與潛在空間分析系統")

# 側邊欄：輸入股票代號
st.sidebar.header("設定")
# 預設放入一些熱門科技股與 ETF
ticker_input = st.sidebar.text_input("請輸入美股代號 (Ticker)", "NVDA").upper()

@st.cache_data(ttl=3600) # 快取資料1小時，避免重複請求
def fetch_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 提取所需財務與價格資訊
        data = {
            "name": info.get("shortName", ticker),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
            "target_mean": info.get("targetMeanPrice", 0),
            "target_high": info.get("targetHighPrice", 0),
            "target_low": info.get("targetLowPrice", 0),
            "analyst_rating": info.get("recommendationKey", "N/A").capitalize()
        }
        return data
    except Exception as e:
        return None

if ticker_input:
    with st.spinner(f"正在載入 {ticker_input} 的資料..."):
        data = fetch_stock_data(ticker_input)
        
        if data and data['current_price'] > 0:
            st.subheader(f"📊 {data['name']} ({ticker_input})")
            
            # 判斷是否有目標價資料 (個股 vs ETF)
            if data.get('target_mean') and data['target_mean'] > 0:
                # ===== 這是個股：有目標價，顯示完整分析 =====
                upside_mean = ((data['target_mean'] - data['current_price']) / data['current_price']) * 100
                upside_high = ((data['target_high'] - data['current_price']) / data['current_price']) * 100
                upside_low = ((data['target_low'] - data['current_price']) / data['current_price']) * 100
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("目前股價", f"${data['current_price']:.2f}", f"評級: {data['analyst_rating']}")
                col2.metric("分析師平均目標價", f"${data['target_mean']:.2f}", f"{upside_mean:.2f}%")
                col3.metric("最高目標價", f"${data['target_high']:.2f}", f"{upside_high:.2f}%")
                col4.metric("最低目標價", f"${data['target_low']:.2f}", f"{upside_low:.2f}%")
                
                st.markdown("### 🎯 目標價區間視覺化")
                fig = go.Figure()
                
                fig.add_trace(go.Indicator(
                    mode = "number+gauge+delta",
                    value = data['current_price'],
                    delta = {'reference': data['target_mean'], 'position': "top"},
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "目前股價 vs 分析師預期"},
                    gauge = {
                        'axis': {'range': [min(data['target_low'], data['current_price']) * 0.9, 
                                           max(data['target_high'], data['current_price']) * 1.1]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, data['target_low']], 'color': "lightcoral"},
                            {'range': [data['target_low'], data['target_high']], 'color': "lightgreen"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': data['target_mean']}
                    }))
                st.plotly_chart(fig, use_container_width=True)
                st.info("💡 綠色區間為分析師預測的最高與最低範圍，紅線為平均目標價。")
                
            else:
                # ===== 這是 ETF 或無預測資料的標的：只顯示股價 =====
                st.success("成功取得報價！但此標的（如 ETF）目前沒有華爾街分析師的目標價預測。")
                col1, col2 = st.columns(2)
                col1.metric("目前股價", f"${data['current_price']:.2f}")
                col2.info("通常大盤指數型 ETF 不會有特定目標價，建議改用定期定額等長期策略評估。")
                
        else:
            st.error("無法取得資料，請確認您輸入的美股代號是否正確（例如輸入 AAPL 而非蘋果）。")
