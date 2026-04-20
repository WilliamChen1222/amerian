import streamlit as st
import yfinance as yf

# 1. 網頁基本設定
st.set_page_config(page_title="美股智慧量化估值系統", layout="wide")

# 2. 記憶狀態初始化 (確保清單與選擇不因重新整理而消失)
if 'watch_list' not in st.session_state:
    st.session_state.watch_list = ["NVDA", "PLTR", "TSM", "AAPL", "MSFT"]

if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "NVDA"

# ==========================================
# 3. 側邊欄：我的追蹤清單管理
# ==========================================
with st.sidebar:
    st.header("📋 我的追蹤清單")

    # 新增功能
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        new_item = st.text_input("新增代號", label_visibility="collapsed", placeholder="例如: GOOG")
    with col_btn:
        if st.button("➕", use_container_width=True) and new_item:
            if new_item.upper() not in st.session_state.watch_list:
                st.session_state.watch_list.append(new_item.upper())
                st.rerun()

    st.divider()

    # 清單列表與操作
    for i, item in enumerate(st.session_state.watch_list):
        col_text, col_up, col_down, col_del = st.columns([4, 1, 1, 1])
        
        with col_text:
            # 點擊名稱即可切換主畫面分析對象
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
# 4. 主畫面：智慧量化估值系統
# ==========================================
st.title("🛡️ 美股智慧量化估值系統")

# 輸入框連動側邊欄
ticker_symbol = st.text_input("請輸入美股代號進行分析", value=st.session_state.current_ticker).upper()

if ticker_symbol:
    st.session_state.current_ticker = ticker_symbol
    
    with st.spinner(f"系統正在連線華爾街資料庫，分析 {ticker_symbol}..."):
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            
            # 基本資料擷取
            name = info.get("shortName", ticker_symbol)
            current_price = info.get("currentPrice", 0)
            trailing_eps = info.get("trailingEps", 0)   # 過去12個月真實EPS
            forward_eps = info.get("forwardEps", 0)      # 未來12個月預估EPS
            forward_pe = info.get("forwardPE", 0)        # 目前預估P/E
            
            st.subheader(f"📊 {name} ({ticker_symbol})")
            
            if current_price > 0:
                # 顯示目前即時報價
                st.metric("目前即時股價", f"${current_price:.2f}")
                
                st.divider()

                # --- 智慧預測模型邏輯 ---
                if forward_eps and trailing_eps > 0 and forward_eps > trailing_eps:
                    
                    st.write("### 🧠 智慧量化模型分析 (PEG 估值法)")
                    st.caption("本模型自動抓取華爾街機構共識數據，計算公司成長性與股價的匹配度。")

                    # 1. 自動計算市場共識成長率 (Forward EPS vs Trailing EPS)
                    auto_growth_rate = ((forward_eps - trailing_eps) / trailing_eps) * 100
                    
                    # 2. 自動計算目前 PEG (本益成長比)
                    current_peg = forward_pe / auto_growth_rate
                    
                    # 3. 系統推算合理 P/E (基於 PEG = 1.5 的科技股標準環境)
                    # 您也可以在這裡加入一個 slider 讓自己微調 PEG 基準
                    peg_benchmark = 1.5 
                    smart_target_pe = auto_growth_rate * peg_benchmark
                    
                    # 4. 最終計算目標價
                    smart_target_price = forward_eps * smart_target_pe
                    smart_upside = ((smart_target_price - current_price) / current_price) * 100

                    # 顯示核心量化指標
                    c1, c2, c3 = st.columns(3)
                    c1.metric("共識 EPS 成長率", f"{auto_growth_rate:.2f}%")
                    c2.metric("目前 PEG 值", f"{current_peg:.2f}", delta="估值過高" if current_peg > 2 else "估值合理", delta_color="inverse")
                    c3.metric("智慧推算合理 P/E", f"{smart_target_pe:.2f}x")

                    st.write("#### 💡 系統智慧評估結論")
                    st.markdown(f"""
                    基於 **{auto_growth_rate:.2f}%** 的預期盈餘成長力道：
                    - 如果市場給予匹配成長的合理估值 (PEG={peg_benchmark})，合理本益比應為 **{smart_target_pe:.2f} 倍**。
                    """)
                    
                    if smart_upside > 0:
                        st.success(f"🎯 **智慧推算目標價：${smart_target_price:.2f}** (預期漲幅: **+{smart_upside:.2f}%**)")
                        st.balloons()
                    else:
                        st.warning(f"⚠️ **系統提醒：目前股價可能已預支成長，合理回歸價為：${smart_target_price:.2f}** (目前溢價: **{smart_upside:.2f}%**)")

                else:
                    st.warning("⚠️ 此標的目前獲利成長動能不足、正在虧損或為 ETF，智慧成長模型不適用。")
                    st.info("建議參考目前股價與歷史本益比區間進行判斷。")
            
        except Exception as e:
            st.error(f"資料擷取失敗，請確認代號是否正確。錯誤訊息: {e}")
