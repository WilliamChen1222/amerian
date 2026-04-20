import streamlit as st
import yfinance as yf

st.set_page_config(page_title="美股估值與追蹤系統", layout="wide")

# ==========================================
# 1. 側邊欄：我的追蹤清單系統
# ==========================================
with st.sidebar:
    st.header("📋 我的追蹤清單")
    
    # 初始化 Session State (建立短期記憶)
    if 'watch_list' not in st.session_state:
        st.session_state.watch_list = ["NVDA", "PLTR", "TSM"]
    
    # 記錄目前主畫面正在查看的標的
    if 'current_ticker' not in st.session_state:
        st.session_state.current_ticker = "NVDA"

    # 新增紀錄的輸入框
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        new_item = st.text_input("新增標的", label_visibility="collapsed", placeholder="例如: AAPL")
    with col_btn:
        if st.button("➕", use_container_width=True) and new_item:
            if new_item.upper() not in st.session_state.watch_list:
                st.session_state.watch_list.append(new_item.upper())
                st.rerun()
                
    st.divider()

    # 顯示與管理清單
    for i, item in enumerate(st.session_state.watch_list):
        # 切割版面：按鈕(寬) / 往上 / 往下 / 刪除
        col_text, col_up, col_down, col_del = st.columns([4, 1, 1, 1])
        
        with col_text:
            # 將清單變成按鈕，點擊後更新主畫面的股票
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
# 2. 主畫面：美股 EPS & P/E 估值系統
# ==========================================
st.title("🎯 美股 EPS & P/E 估值系統")

# 主畫面的輸入框，預設值連動側邊欄點擊的標的
ticker_symbol = st.text_input("目前查詢標的 (或手動輸入)", value=st.session_state.current_ticker).upper()

if ticker_symbol:
    # 確保手動輸入時也能更新當前狀態
    st.session_state.current_ticker = ticker_symbol 
    
    with st.spinner(f"正在載入 {ticker_symbol} 的財務數據..."):
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        name = info.get("shortName", ticker_symbol)
        current_price = info.get("currentPrice", 0)
        fwd_eps = info.get("forwardEps", 0)
        fwd_pe = info.get("forwardPE", 0)
        
        st.subheader(f"📊 {name} ({ticker_symbol})")
        
        if fwd_eps and fwd_pe:
            calculated_target = fwd_eps * fwd_pe
            upside = ((calculated_target - current_price) / current_price) * 100
            
            col1, col2, col3 = st.columns(3)
            col1.metric("目前股價", f"${current_price:.2f}")
            col2.metric("預估 EPS (Forward)", f"${fwd_eps:.2f}")
            col3.metric("預估本益比 (Forward)", f"{fwd_pe:.2f}x")
            
            st.divider()
            
            st.write(f"### 💡 估值結論")
            st.write(f"根據分析師預估之 EPS (${fwd_eps:.2f}) 與目前市場給予的 P/E ({fwd_pe:.2f}x)，")
            st.info(f"目前的合理目標價推估為：**${calculated_target:.2f}** (潛在空間: {upside:.2f}%)")
            
        else:
            st.warning("無法取得該標的的預估 EPS 或 P/E 數據（常見於 ETF 或虧損中的公司）。")
            if current_price:
                st.metric("目前股價", f"${current_price:.2f}")
