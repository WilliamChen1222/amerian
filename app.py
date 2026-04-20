import streamlit as st
import yfinance as yf

# 設定網頁標題與版面寬度
st.set_page_config(page_title="美股預測與追蹤系統", layout="wide")

# ==========================================
# 1. 狀態初始化 (短期記憶)
# ==========================================
# 確保網頁重新整理時，清單和目前查詢的股票不會不見
if 'watch_list' not in st.session_state:
    st.session_state.watch_list = ["NVDA", "PLTR", "TSM"]
    
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "NVDA"


# ==========================================
# 2. 側邊欄：我的追蹤清單系統
# ==========================================
with st.sidebar:
    st.header("📋 我的追蹤清單")

    # 新增紀錄的輸入框
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        new_item = st.text_input("新增標的", label_visibility="collapsed", placeholder="例如: AAPL")
    with col_btn:
        if st.button("➕", use_container_width=True) and new_item:
            if new_item.upper() not in st.session_state.watch_list:
                st.session_state.watch_list.append(new_item.upper())
                st.rerun() # 重新載入網頁以更新畫面
                
    st.divider()

    # 顯示與管理清單 (包含上下移動與刪除)
    for i, item in enumerate(st.session_state.watch_list):
        col_text, col_up, col_down, col_del = st.columns([4, 1, 1, 1])
        
        with col_text:
            # 清單按鈕：點擊後更新主畫面的股票
            if st.button(f"**{item}**", key=f"btn_{i}", use_container_width=True):
                st.session_state.current_ticker = item
                st.rerun()
                
        with col_up:
            if i > 0 and st.button("⬆️", key=f"up_{i}"):
                st.session_state.watch_list[i], st.session_state.watch_list[i-1] = st.session_state.watch_list[i-1], st.session_state.watch_list[i]
                st.rerun()
                
        with col_down:
            if i < len(st.session_state.watch_list) - 1 and st.button("⬇️", key=f"down_{i}"):
                st.session_state.watch_list[i], st.session_state.watch_list[i+1] = st.session_state.watch_list[i+1], st.session_state.watch_list[i]
                st.rerun()
                
        with col_del:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.watch_list.pop(i)
                st.rerun()


# ==========================================
# 3. 主畫面：美股預測與估值系統
# ==========================================
st.title("🎯 美股預測與估值系統")

# 主畫面的輸入框，預設值連動側邊欄點擊的標的
ticker_symbol = st.text_input("目前查詢標的 (或手動輸入)", value=st.session_state.current_ticker).upper()

if ticker_symbol:
    # 確保手動輸入時也能更新當前狀態
    st.session_state.current_ticker = ticker_symbol 
    
    with st.spinner(f"正在載入 {ticker_symbol} 的財務數據..."):
        # 抓取 Yahoo Finance 數據
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        name = info.get("shortName", ticker_symbol)
        current_price = info.get("currentPrice", 0)
        fwd_eps = info.get("forwardEps", 0)
        fwd_pe = info.get("forwardPE", 0)
        
        st.subheader(f"📊 {name} ({ticker_symbol})")
        
        # 判斷是否有足夠的資料進行估值 (ETF 或虧損公司通常沒有預估 EPS)
        if fwd_eps and fwd_pe and current_price:
            
            # 顯示基本數據
            col1, col2, col3 = st.columns(3)
            col1.metric("目前股價", f"${current_price:.2f}")
            col2.metric("目前預估 EPS", f"${fwd_eps:.2f}")
            col3.metric("目前市場 P/E", f"{fwd_pe:.2f}x")
            
            st.divider()
            
            # 互動預測區塊
            st.write("### 🔮 一年後目標價預測模型")
            st.info("請調整下方參數，模擬未來的營收成長與市場給予的估值倍數。")
            
            col_slider1, col_slider2 = st.columns(2)
            with col_slider1:
                expected_growth = st.slider("預估未來一年 EPS 成長率 (%)", min_value=-20, max_value=100, value=15, step=1)
            with col_slider2:
                target_pe = st.slider("設定目標合理本益比 (倍)", min_value=5.0, max_value=100.0, value=float(fwd_pe), step=0.5)
            
            # 核心預測公式計算
            future_eps = fwd_eps * (1 + (expected_growth / 100))
            calculated_target = future_eps * target_pe
            upside = ((calculated_target - current_price) / current_price) * 100
            
            # 顯示結論
            st.write("#### 💡 估值結論")
            st.write(f"若該公司 EPS 成長 **{expected_growth}%** 達到 **${future_eps:.2f}**，且市場願意給予 **{target_pe} 倍** 的本益比：")
            
            if upside > 0:
                st.success(f"📈 預測一年後目標價為：**${calculated_target:.2f}** (潛在空間: **+{upside:.2f}%**)")
            else:
                st.error(f"📉 預測一年後目標價為：**${calculated_target:.2f}** (潛在空間: **{upside:.2f}%**)")
            
        else:
            st.warning("無法取得該標的完整的預估 EPS 或 P/E 數據（常見於 ETF 或目前未獲利的公司）。")
            if current_price:
                st.metric("目前股價", f"${current_price:.2f}")
