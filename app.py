import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 網頁基本設定
st.set_page_config(page_title="美股智慧量化估值系統", layout="wide")

# ==========================================
# 2. 核心功能：批次數據抓取與智慧排序
# ==========================================
@st.cache_data(ttl=300)
def fetch_batch_data(tickers):
    data = {}
    for t in tickers:
        try:
            info = yf.Ticker(t).info
            price = info.get("currentPrice", 0)
            pe = info.get("forwardPE", 0)
            fwd_eps = info.get("forwardEps", 0)
            trail_eps = info.get("trailingEps", 0)
            
            # 計算初始智慧預期漲幅 (含55x P/E天花板)
            upside = 0
            if fwd_eps and trail_eps > 0 and fwd_eps > trail_eps and price > 0:
                growth = ((fwd_eps - trail_eps) / trail_eps) * 100
                target_pe = min(growth * 1.5, 55.0) 
                target_price = fwd_eps * target_pe
                upside = ((target_price - price) / price) * 100
                
            data[t] = {"price": price, "pe": pe, "upside": upside}
        except:
            data[t] = {"price": 0, "pe": 0, "upside": -999} 
    return data

# 3. 記憶狀態初始化
if 'watch_list' not in st.session_state:
    # 預設清單包含您關注的熱門標的與指數
    st.session_state.watch_list = ["NVDA", "PLTR", "TSM", "AAPL", "MSFT", "VOO", "QQQ"]

if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "NVDA"

# ==========================================
# 4. 側邊欄：清單管理與自動排序
# ==========================================
with st.sidebar:
    st.header("📋 我的追蹤清單")
    
    # 新增標的
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        new_item = st.text_input("新增代號", label_visibility="collapsed", placeholder="例如: GOOG")
    with col_btn:
        if st.button("➕", use_container_width=True) and new_item:
            if new_item.upper() not in st.session_state.watch_list:
                st.session_state.watch_list.append(new_item.upper())
                st.rerun()

    st.divider()
    
    # 自動排序功能
    st.write("📊 **智慧排序**")
    sort_option = st.selectbox("選擇條件", ["選擇條件...", "股價 (高➡️低)", "預期漲幅 (高➡️低)", "本益比 (低➡️高)"])
    if st.button("執行排序", use_container_width=True):
        if sort_option != "選擇條件...":
            with st.spinner("同步最新數據中..."):
                metrics = fetch_batch_data(st.session_state.watch_list)
                if sort_option == "股價 (高➡️低)":
                    st.session_state.watch_list.sort(key=lambda x: metrics[x]["price"], reverse=True)
                elif sort_option == "預期漲幅 (高➡️低)":
                    st.session_state.watch_list.sort(key=lambda x: metrics[x]["upside"], reverse=True)
                elif sort_option == "本益比 (低➡️高)":
                    st.session_state.watch_list.sort(key=lambda x: metrics[x]["pe"] if metrics[x]["pe"] > 0 else 9999)
            st.rerun()
    
    st.divider()
    
    # 清單列表操作 (手動排序與刪除)
    for i, item in enumerate(st.session_state.watch_list):
        c_text, c_up, c_down, c_del = st.columns([4, 1, 1, 1])
        with c_text:
            if st.button(f"**{item}**", key=f"btn_{i}", use_container_width=True):
                st.session_state.current_ticker = item
                st.rerun()
        with c_up:
            if i > 0 and st.button("⬆️", key=f"up_{i}"):
                st.session_state.watch_list[i], st.session_state.watch_list[i-1] = st.session_state.watch_list[i-1], st.session_state.watch_list[i]
                st.rerun()
        with c_down:
            if i < len(st.session_state.watch_list) - 1 and st.button("⬇️", key=f"down_{i}"):
                st.session_state.watch_list[i], st.session_state.watch_list[i+1] = st.session_state.watch_list[i+1], st.session_state.watch_list[i]
                st.rerun()
        with c_del:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.watch_list.pop(i)
                st.rerun()

# ==========================================
# 5. 主畫面：真實世界多階段預測模型
# ==========================================
st.title("🛡️ 美股智慧量化估值系統")

ticker_symbol = st.text_input("請輸入美股代號進行分析", value=st.session_state.current_ticker).upper()

if ticker_symbol:
    st.session_state.current_ticker = ticker_symbol
    with st.spinner(f"正在連線華爾街資料庫分析 {ticker_symbol}..."):
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            name = info.get("shortName", ticker_symbol)
            current_price = info.get("currentPrice", 0)
            trailing_eps = info.get("trailingEps", 0)
            forward_eps = info.get("forwardEps", 0)
            forward_pe = info.get("forwardPE", 0)
            
            st.subheader(f"📊 {name} ({ticker_symbol})")
            if current_price > 0:
                st.metric("目前即時股價", f"${current_price:.2f}")
                st.divider()

                # 判斷是否適用成長模型
                if forward_eps and trailing_eps > 0 and forward_eps > trailing_eps:
                    st.write("### 🧠 真實世界長線衰退模型分析")
                    st.caption("模型參數：P/E 上限 55x、終端成長率回歸 6%、終端 P/E 回歸 25x、年通膨率 3%。")
                    
                    # 1. 初始參數計算 (第1年)
                    initial_growth = ((forward_eps - trailing_eps) / trailing_eps) * 100
                    initial_pe = min(initial_growth * 1.5, 55.0) 
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("初始 EPS 成長率", f"{initial_growth:.2f}%")
                    c2.metric("初始推算 P/E", f"{initial_pe:.2f}x", delta="已觸發上限" if initial_growth * 1.5 > 55 else None)
                    c3.metric("目前 PEG 值", f"{forward_pe / initial_growth:.2f}")

                    # 2. 模擬未來 10 年 (衰退模型)
                    terminal_growth = 6.0
                    terminal_pe = 25.0
                    inflation_rate = 3.0
                    
                    projection_data = []
                    temp_eps = forward_eps
                    
                    for year in range(1, 11):
                        # 線性衰退係數 (0 到 1)
                        decay = (year - 1) / 9.0
                        
                        # 當年成長率與 P/E 隨時間滑落
                        curr_growth = initial_growth - (initial_growth - terminal_growth) * decay
                        curr_pe = initial_pe - (initial_pe - terminal_pe) * decay
                        
                        if year > 1:
                            temp_eps = temp_eps * (1 + curr_growth / 100)
                        
                        # 名目股價與實質股價 (扣除通膨)
                        nominal_price = temp_eps * curr_pe
                        real_price = nominal_price / ((1 + inflation_rate / 100) ** year)
                        real_return = ((real_price - current_price) / current_price) * 100
                        
                        if year in [1, 2, 3, 5, 10]:
                            projection_data.append({
                                "時間": f"{year} 年後",
                                "預估成長率": f"{curr_growth:.1f}%",
                                "合理 P/E": f"{curr_pe:.1f}x",
                                "名目股價": f"${nominal_price:.2f}",
                                "實質價值 (扣通膨)": f"${real_price:.2f}",
                                "實質報酬率": f"{real_return:.2f}%"
                            })
                    
                    st.table(pd.DataFrame(projection_data))
                    st.info("💡 註：'實質價值' 代表將未來的錢換算成現在購買力的價值，這才是最準確的投資參考。")

                else:
                    st.warning("⚠️ 此標的獲利成長動能不足、目前虧損或為 ETF，不適用智慧成長模型。")
                    st.info(f"該標的目前預估 P/E 為 {forward_pe:.2f}x，建議參考歷史區間評估。")
            
        except Exception as e:
            st.error(f"分析失敗，請檢查代號是否正確。錯誤代碼: {e}")
