import streamlit as st
import yfinance as yf

# 1. 網頁基本設定
st.set_page_config(page_title="美股核心估值戰情板", layout="wide")

# 2. 記憶狀態初始化
if 'watch_list' not in st.session_state:
    st.session_state.watch_list = ["NVDA", "PLTR", "TSM", "AAPL", "MSFT", "VOO"]

if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "NVDA"

# ==========================================
# 3. 側邊欄：極簡追蹤清單
# ==========================================
with st.sidebar:
    st.header("📋 追蹤清單")
    
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        new_item = st.text_input("新增代號", label_visibility="collapsed", placeholder="例如: GOOG")
    with col_btn:
        if st.button("➕", use_container_width=True) and new_item:
            if new_item.upper() not in st.session_state.watch_list:
                st.session_state.watch_list.append(new_item.upper())
                st.rerun()

    st.divider()
    
    for i, item in enumerate(st.session_state.watch_list):
        c_text, c_del = st.columns([4, 1])
        with c_text:
            if st.button(f"**{item}**", key=f"btn_{i}", use_container_width=True):
                st.session_state.current_ticker = item
                st.rerun()
        with c_del:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.watch_list.pop(i)
                st.rerun()

# ==========================================
# 4. 主畫面：五大核心數據儀表板
# ==========================================
st.title("🎯 美股核心估值戰情板")
st.markdown("專注於當下估值與短期成長動能，捨棄無效的長線預測。")

ticker_symbol = st.text_input("請輸入美股代號進行分析", value=st.session_state.current_ticker).upper()

if ticker_symbol:
    st.session_state.current_ticker = ticker_symbol
    with st.spinner(f"正在擷取 {ticker_symbol} 的最新核心數據..."):
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            name = info.get("shortName", ticker_symbol)
            
            # 抓取原始數據
            current_price = info.get("currentPrice", 0)
            forward_eps = info.get("forwardEps", 0)
            forward_pe = info.get("forwardPE", 0)
            trailing_eps = info.get("trailingEps", 0)
            
            st.subheader(f"📊 {name} ({ticker_symbol})")
            
            if current_price > 0:
                # 計算成長率與 PEG
                growth_rate = 0
                peg_ratio = 0
                if forward_eps and trailing_eps and trailing_eps > 0 and forward_eps > trailing_eps:
                    growth_rate = ((forward_eps - trailing_eps) / trailing_eps) * 100
                    if growth_rate > 0:
                        peg_ratio = forward_pe / growth_rate

                # --- 第一排：價格與絕對估值 ---
                st.write("### 💰 基礎估值指標")
                col1, col2, col3 = st.columns(3)
                col1.metric("現在股價 (Current Price)", f"${current_price:.2f}")
                
                if forward_eps:
                    col2.metric("預估每股盈餘 (Forward EPS)", f"${forward_eps:.2f}", "未來 12 個月預期")
                else:
                    col2.metric("預估每股盈餘 (Forward EPS)", "無資料")
                    
                if forward_pe:
                    col3.metric("預估本益比 (Forward P/E)", f"{forward_pe:.2f}x", "市場目前給予的定價倍數")
                else:
                    col3.metric("預估本益比 (Forward P/E)", "無資料")

                st.divider()

                # --- 第二排：成長與相對估值 ---
                st.write("### 🚀 成長動能指標 (PEG 模型)")
                if growth_rate > 0 and peg_ratio > 0:
                    col4, col5 = st.columns(2)
                    col4.metric("預期成長率 (Expected Growth)", f"{growth_rate:.2f}%", "基於近四季與未來預估之增幅")
                    
                    # 依據 PEG 給予不同的顏色與提示
                    if peg_ratio <= 1.0:
                        peg_status = "被低估 (強烈吸引力)"
                        delta_color = "normal"
                    elif peg_ratio <= 1.5:
                        peg_status = "估值合理 (具備投資價值)"
                        delta_color = "off"
                    elif peg_ratio <= 2.0:
                        peg_status = "估值偏高 (需注意風險)"
                        delta_color = "inverse"
                    else:
                        peg_status = "估值過熱 (透支未來成長)"
                        delta_color = "inverse"
                        
                    col5.metric("本益成長比 (PEG Ratio)", f"{peg_ratio:.2f}", peg_status, delta_color=delta_color)
                    
                    # 簡單明瞭的白話文結論
                    st.info(f"**戰情解讀**：市場預期該公司未來盈餘將成長 **{growth_rate:.1f}%**。結合目前 **{forward_pe:.1f} 倍** 的本益比，得出 PEG 值為 **{peg_ratio:.2f}**，目前的定價狀態屬於「**{peg_status}**」。")
                    
                else:
                    st.warning("⚠️ 此標的目前缺乏足夠的 EPS 成長數據，或呈現衰退，無法計算預期成長率與 PEG。建議直接參考歷史本益比區間。")
                    
        except Exception as e:
            st.error(f"資料擷取失敗，請確認代號是否正確。錯誤訊息: {e}")
