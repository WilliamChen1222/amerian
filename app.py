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
        
        if data and data['current_price'] > 0 and data['target_mean'] > 0:
            st.subheader(f"📊 {data['name']} ({ticker_input})")
            
            # 計算潛在報酬率
            upside_mean = ((data['target_mean'] - data['current_price']) / data['current_price']) * 100
            upside_high = ((data['target_high'] - data['current_price']) / data['current_price']) * 100
            upside_low = ((data['target_low'] - data['current_price']) / data['current_price']) * 100
            
            # 使用 Metric 顯示核心數據
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("目前股價", f"${data['current_price']:.2f}", f"評級: {data['analyst_rating']}")
            col2.metric("分析師平均目標價", f"${data['target_mean']:.2f}", f"{upside_mean:.2f}%")
            col3.metric("最高目標價", f"${data['target_high']:.2f}", f"{upside_high:.2f}%")
            col4.metric("最低目標價", f"${data['target_low']:.2f}", f"{upside_low:.2f}%")
            
            # 視覺化圖表
            st.markdown("### 🎯 目標價區間視覺化")
            fig = go.Figure()
            
            # 畫出目前價格
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
            st.error("無法取得該股票的目標價資訊，可能是輸入錯誤，或是該標的（如多數 ETF）沒有分析師提供目標價。")