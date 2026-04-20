import streamlit as st
import yfinance as yf

# 1. 網頁基本設定
st.set_page_config(page_title="美股智慧量化估值系統", layout="wide")

# ==========================================
# 2. 核心功能：批次抓取與計算數據 (用於排序)
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
            
            upside = 0
            if fwd_eps and trail_eps > 0 and fwd_eps > trail_eps and price > 0:
                growth = ((fwd_eps - trail_eps) / trail_eps) * 100
                target_pe = growth * 1.5
                target_price = fwd_eps * target_pe
                upside = ((target_price - price) / price) * 100
                
            data[t] = {"price": price, "pe": pe, "upside": upside}
        except:
            data[t] = {"price": 0, "pe": 0, "upside": -999} 
    return data

# 3. 記憶狀態初始化
if 'watch_list' not in st.session_state:
    st.session_state.watch_list = ["NVDA", "PLTR", "TSM", "AAPL", "MSFT"]

if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "NVDA"

# ==========================================
# 4. 側邊欄：我的追蹤清單管理 (包含排序功能)
# ==========================================
with st.sidebar:
    st.header("📋 我的追蹤清單")

    col_input, col_btn = st.columns([4, 1])
    with col_input:
        new_item = st.text_input("新增代號", label_visibility="collapsed", placeholder="例如: GOOG")
    with col_btn:
        if st.button("➕", use_container_width=True) and new_item:
            if new_item.upper() not in st.session_state.watch_list:
                st.session_state.watch_list.append(new_item.upper())
                st.rerun()

    st.divider()

    st.write("📊 **自動排序清單**")
    sort_col1, sort_col2 = st.columns([2, 1])
    with sort_col1:
        sort_option = st.selectbox(
            "選擇排序條件", 
            ["選擇條件...", "股價 (高➡️低)", "預期漲幅 (高➡️低)", "本益比 (低➡️高)"], 
            label_visibility="collapsed"
        )
    with sort_col2:
        if st.button("排序", use_container_width=True):
            if sort_option != "選擇條件...":
                with st.spinner("連線華爾街抓取數據中..."):
                    metrics = fetch_batch_data(st.session_state.watch_list)
                    
                    if sort_option == "股價 (高➡️低)":
                        st.session_state.watch_list.sort(key=lambda x: metrics[x]["price"], reverse=True)
                    elif sort_option == "預期漲幅 (高➡️低)":
                        st.session_state.watch_list.sort(key=lambda x: metrics[x]["upside"], reverse=True)
                    elif sort_option == "本益比 (低➡️高)":
                        st.session_state.watch_list.sort(key=lambda x: metrics[x]["pe"] if metrics[x]["pe"] > 0 else 9999)
                
                st.rerun()
    
    st.caption("💡 提示：自動排序後，您依然可以使用下方的 ⬆️⬇️ 按鈕微調。")
    st.divider()

    for i, item in enumerate(st.session_state.watch_list):
        col_text, col_up, col_down, col_del = st.columns([4, 1, 1, 1])
        
        with col_text:
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
# 5. 主畫面：智慧量化估值系統
# ==========================================
st.title("🛡️ 美股智慧量化估值系統")

ticker_symbol = st.text_input("請輸入美股代號進行分析", value=st.session_state.current_ticker).upper()

if ticker_symbol:
    st.session_state.current_ticker = ticker_symbol
    
    with st.spinner(f"系統正在連線華爾街資料庫，分析 {ticker_symbol}..."):
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

                if forward_eps and trailing_eps > 0 and forward_eps > trailing_eps:
                    st.write("### 🧠 智慧量化模型分析 (PEG 估值法)")
                    st.caption("本模型自動抓取華爾街機構共識數據，計算公司成長性與股價的匹配度。")

                    auto_growth_rate = ((forward_eps - trailing_eps) / trailing_eps) * 100
                    current_peg = forward_pe / auto_growth_rate
                    peg_benchmark = 1.5 
                    smart_target_pe = auto_growth_rate * peg_benchmark
                    smart_target_price = forward_eps * smart_target_pe
                    smart_upside = ((smart_target_price - current_price) / current_price) * 100

                    c1, c2, c3 = st.columns(3)
                    c1.metric("共識 EPS 成長率", f"{auto_growth_rate:.2f}%")
                    c2.metric("目前 PEG 值", f"{current_peg:.2f}", delta="估值偏高" if current_peg > 2 else "估值合理", delta_color="inverse")
                    c3.metric("智慧推算合理 P/E", f"{smart_target_pe:.2f}x")

                    st.write("#### 💡 系統智慧評估結論")
                    st.markdown(f"""
                    基於 **{auto_growth_rate:.2f}%** 的預期盈餘成長力道：
                    - 如果市場給予匹配成長的合理估值 (PEG={peg_benchmark})，合理本益比應為 **{smart_target_pe:.2f} 倍**。
                    """)
                    
                    if smart_upside > 0:
                        st.success(f"🎯 **智慧推算目標價：${smart_target_price:.2f}** (預期空間: **+{smart_upside:.2f}%**)")
                        # 已取消氣球特效
                    else:
                        st.warning(f"⚠️ **系統提醒：目前股價可能已透支成長，合理回歸價為：${smart_target_price:.2f}** (目前溢價: **{smart_upside:.2f}%**)")

                else:
                    st.warning("⚠️ 此標的目前獲利成長動能不足、正在虧損或為 ETF，智慧成長模型不適用。")
                    st.info("建議參考目前股價與歷史本益比區間進行判斷。")
            
        except Exception as e:
            st.error(f"資料擷取失敗，請確認代號是否正確。錯誤訊息: {e}")
