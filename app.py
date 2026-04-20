import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 網頁基本設定
st.set_page_config(page_title="美股智慧量化估值系統", layout="wide")

# 2. 核心功能：批次數據抓取
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
                # 這裡也同步套用 55 倍天花板
                target_pe = min(growth * 1.5, 55.0) 
                target_price = fwd_eps * target_pe
                upside = ((target_price - price) / price) * 100
                
            data[t] = {"price": price, "pe": pe, "upside": upside}
        except:
            data[t] = {"price": 0, "pe": 0, "upside": -999} 
    return data

# 3. 記憶狀態初始化
if 'watch_list' not in st.session_state:
    st.session_state.watch_list = ["NVDA", "PLTR", "TSM", "AAPL", "VOO", "QQQ"]

if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "NVDA"

# ==========================================
# 4. 側邊欄：清單與排序
# ==========================================
with st.sidebar:
    st.header("📋 我的追蹤清單")
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        new_item = st.text_input("新增代號", label_visibility="collapsed", placeholder="例如: MSFT")
    with col_btn:
        if st.button("➕", use_container_width=True) and new_item:
            if new_item.upper() not in st.session_state.watch_list:
                st.session_state.watch_list.append(new_item.upper())
                st.rerun()

    st.divider()
    st.write("📊 **自動排序清單**")
    sort_option = st.selectbox("選擇排序條件", ["選擇條件...", "股價 (高➡️低)", "預期漲幅 (高➡️低)", "本益比 (低➡️高)"])
    if st.button("執行排序", use_container_width=True):
        if sort_option != "選擇條件...":
            with st.spinner("更新數據中..."):
                metrics = fetch_batch_data(st.session_state.watch_list)
                if sort_option == "股價 (高➡️低)":
                    st.session_state.watch_list.sort(key=lambda x: metrics[x]["price"], reverse=True)
                elif sort_option == "預期漲幅 (高➡️低)":
                    st.session_state.watch_list.sort(key=lambda x: metrics[x]["upside"], reverse=True)
                elif sort_option == "本益比 (低➡️高)":
                    st.session_state.watch_list.sort(key=lambda x: metrics[x]["pe"] if metrics[x]["pe"] > 0 else 9999)
            st.rerun()
    
    st.divider()
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
# 5. 主畫面：智慧估值與複利預測
# ==========================================
st.title("🛡️ 美股智慧量化估值系統")

ticker_symbol = st.text_input("請輸入美股代號進行分析", value=st.session_state.current_ticker).upper()

if ticker_symbol:
    st.session_state.current_ticker = ticker_symbol
    with st.spinner(f"分析中..."):
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
                    st.write("### 🧠 智慧量化模型分析 (已加入 55x P/E 天花板)")
                    
                    # 成長率與智慧 P/E 計算
                    auto_growth_rate = ((forward_eps - trailing_eps) / trailing_eps) * 100
                    raw_target_pe = auto_growth_rate * 1.5
                    # 核心改動：加入 55 倍上限
                    smart_target_pe = min(raw_target_pe, 55.0) 
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("共識 EPS 成長率", f"{auto_growth_rate:.2f}%")
                    c2.metric("智慧推算合理 P/E", f"{smart_target_pe:.2f}x", delta="已達天花板" if raw_target_pe > 55 else None)
                    c3.metric("目前 PEG 值", f"{forward_pe / auto_growth_rate:.2f}")

                    # --- 10年預測表 ---
                    st.write("#### ⏳ 長線複利股價預測")
                    projection_data = []
                    for year in [1, 2, 5, 10]:
                        # 複利公式：Year 1 使用 Forward EPS，之後每年按成長率複利
                        future_eps = forward_eps * ((1 + auto_growth_rate/100) ** (year - 1))
                        target_price = future_eps * smart_target_pe
                        total_return = ((target_price - current_price) / current_price) * 100
                        projection_data.append({
                            "預測時間": f"{year} 年後",
                            "預估每股盈餘 (EPS)": f"${future_eps:.2f}",
                            "目標股價推算": f"${target_price:.2f}",
                            "累計預期報酬率": f"{total_return:.2f}%"
                        })
                    
                    st.table(pd.DataFrame(projection_data))
                    st.caption(f"💡 註：1年後預估係基於 Forward EPS 乘上合理 P/E。2年起假設公司維持相同成長動能進行複利計算。")

                else:
                    st.warning("⚠️ 此標的獲利成長動能不足或為 ETF，不適用智慧成長模型。")
            
        except Exception as e:
            st.error(f"分析失敗: {e}")
