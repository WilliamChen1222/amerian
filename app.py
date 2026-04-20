import streamlit as st
import yfinance as yf

# 1. 網頁基本設定
st.set_page_config(page_title="美股戰情板與智慧排序", layout="wide")

# ==========================================
# 2. 核心功能：批次抓取數據 (專供排序使用)
# ==========================================
@st.cache_data(ttl=300) # 快取 5 分鐘，避免頻繁按排序被 Yahoo 阻擋
def fetch_batch_data(tickers):
    data = {}
    for t in tickers:
        try:
            info = yf.Ticker(t).info
            # 兼容個股與 ETF 的價格抓取
            price = info.get("currentPrice", info.get("regularMarketPreviousClose", 0))
            fwd_eps = info.get("forwardEps", 0)
            fwd_pe = info.get("forwardPE", 0)
            trail_eps = info.get("trailingEps", 0)
            
            # 計算成長率與 PEG
            growth = 0
            peg = 0
            if fwd_eps and trail_eps and trail_eps > 0 and fwd_eps > trail_eps:
                growth = ((fwd_eps - trail_eps) / trail_eps) * 100
                if growth > 0 and fwd_pe:
                    peg = fwd_pe / growth

            # 存入字典 (若無資料如 ETF，則賦予極端值以便排到清單最後)
            data[t] = {
                "price": price if price else 0,
                "fwd_pe": fwd_pe if fwd_pe else 9999,    # 本益比越低越好，無資料設為 9999
                "fwd_eps": fwd_eps if fwd_eps else -9999, # EPS 越高越好，無資料設為 -9999
                "growth": growth if growth else -9999,
                "peg": peg if peg else 9999              # PEG 越低越好，無資料設為 9999
            }
        except:
            data[t] = {"price": 0, "fwd_pe": 9999, "fwd_eps": -9999, "growth": -9999, "peg": 9999}
    return data

# 3. 記憶狀態初始化
if 'watch_list' not in st.session_state:
    st.session_state.watch_list = ["NVDA", "PLTR", "TSM", "AAPL", "QQQ", "VOO"]

if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "NVDA"

# ==========================================
# 4. 側邊欄：追蹤清單與智慧排序
# ==========================================
with st.sidebar:
    st.header("📋 追蹤清單")
    
    # 新增標的
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        new_item = st.text_input("新增代號", label_visibility="collapsed", placeholder="例如: MSFT")
    with col_btn:
        if st.button("➕", use_container_width=True) and new_item:
            if new_item.upper() not in st.session_state.watch_list:
                st.session_state.watch_list.append(new_item.upper())
                st.rerun()

    st.divider()
    
    # --- 💎 多維度智慧排序 ---
    st.write("📊 **手動更新與排序**")
    sort_option = st.selectbox(
        "選擇排序依據", 
        ["選擇條件...", "💰 股價 (高 ➡️ 低)", "🎯 預估 EPS (高 ➡️ 低)", "🚀 預期成長率 (高 ➡️ 低)", "📉 預估本益比 (低 ➡️ 高)", "🛡️ PEG 估值 (低 ➡️ 高)"],
        label_visibility="collapsed"
    )
    
    if st.button("🔄 更新數據並排序", use_container_width=True):
        if sort_option != "選擇條件...":
            with st.spinner("連線抓取最新數據中..."):
                metrics = fetch_batch_data(st.session_state.watch_list)
                
                # 依照使用者選擇進行排序
                if sort_option == "💰 股價 (高 ➡️ 低)":
                    st.session_state.watch_list.sort(key=lambda x: metrics[x]["price"], reverse=True)
                elif sort_option == "🎯 預估 EPS (高 ➡️ 低)":
                    st.session_state.watch_list.sort(key=lambda x: metrics[x]["fwd_eps"], reverse=True)
                elif sort_option == "🚀 預期成長率 (高 ➡️ 低)":
                    st.session_state.watch_list.sort(key=lambda x: metrics[x]["growth"], reverse=True)
                elif sort_option == "📉 預估本益比 (低 ➡️ 高)":
                    st.session_state.watch_list.sort(key=lambda x: metrics[x]["fwd_pe"])
                elif sort_option == "🛡️ PEG 估值 (低 ➡️ 高)":
                    st.session_state.watch_list.sort(key=lambda x: metrics[x]["peg"])
            st.rerun()

    st.caption("💡 ETF 因缺乏 EPS 預測，排序時會自動置底。")
    st.divider()
    
    # 清單列表 (可點擊切換、手動微調上下、刪除)
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
# 5. 主畫面：五大核心數據儀表板 (含 ETF 兼容)
# ==========================================
st.title("🎯 美股核心估值戰情板")

ticker_symbol = st.text_input("請輸入美股代號進行分析", value=st.session_state.current_ticker).upper()

if ticker_symbol:
    st.session_state.current_ticker = ticker_symbol
    with st.spinner(f"正在擷取 {ticker_symbol} 的最新核心數據..."):
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            name = info.get("shortName", ticker_symbol)
            
            current_price = info.get("currentPrice", info.get("regularMarketPreviousClose", 0))
            forward_eps = info.get("forwardEps", 0)
            forward_pe = info.get("forwardPE", 0)
            trailing_eps = info.get("trailingEps", 0)
            
            st.subheader(f"📊 {name} ({ticker_symbol})")
            
            if current_price > 0:
                # --- 判斷是否為 ETF 或缺乏預估資料的標的 ---
                if not forward_eps or forward_eps == 0:
                    # 呈現 ETF 或大盤模式
                    st.success("✅ 系統偵測此標的為 ETF 或無分析師獲利預估之標的。")
                    col1, col2 = st.columns(2)
                    col1.metric("目前即時報價", f"${current_price:.2f}")
                    
                    # 嘗試抓取 ETF 相關資料 (若無則顯示 N/A)
                    yield_pct = info.get("yield", info.get("dividendYield", 0)) * 100
                    if yield_pct > 0:
                        col2.metric("預估殖利率", f"{yield_pct:.2f}%")
                    else:
                        col2.metric("標的類型", "指數型基金 / ETF")
                        
                    st.info("💡 投資 ETF 首重「長期年化報酬率」與「內扣費用率」，因其為一籃子股票，故不適用單一公司的 P/E 與 PEG 估值模型。")
                
                else:
                    # 呈現個股模式
                    growth_rate = 0
                    peg_ratio = 0
                    if trailing_eps > 0 and forward_eps > trailing_eps:
                        growth_rate = ((forward_eps - trailing_eps) / trailing_eps) * 100
                        if growth_rate > 0 and forward_pe:
                            peg_ratio = forward_pe / growth_rate

                    st.write("### 💰 基礎估值指標")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("現在股價 (Price)", f"${current_price:.2f}")
                    col2.metric("預估每股盈餘 (Fwd EPS)", f"${forward_eps:.2f}")
                    col3.metric("預估本益比 (Fwd P/E)", f"{forward_pe:.2f}x")

                    st.divider()

                    st.write("### 🚀 成長動能指標 (PEG 模型)")
                    if growth_rate > 0 and peg_ratio > 0:
                        col4, col5 = st.columns(2)
                        col4.metric("預期成長率 (Growth)", f"{growth_rate:.2f}%")
                        
                        if peg_ratio <= 1.0:
                            peg_status, delta_color = "被低估 (強烈吸引力)", "normal"
                        elif peg_ratio <= 1.5:
                            peg_status, delta_color = "估值合理", "off"
                        else:
                            peg_status, delta_color = "估值偏高 (需注意風險)", "inverse"
                            
                        col5.metric("本益成長比 (PEG Ratio)", f"{peg_ratio:.2f}", peg_status, delta_color=delta_color)
                        st.info(f"**戰情解讀**：市場預期未來盈餘成長 **{growth_rate:.1f}%**。結合目前 **{forward_pe:.1f} 倍** 的本益比，得出 PEG 值為 **{peg_ratio:.2f}**，目前的定價狀態屬於「**{peg_status}**」。")
                    else:
                        st.warning("⚠️ 此標的目前缺乏足夠的 EPS 成長數據，或呈現衰退，無法計算預期成長率與 PEG。")
                        
        except Exception as e:
            st.error(f"資料擷取失敗，請確認代號是否正確。錯誤訊息: {e}")
