# ==========================================
# 5. 主畫面：真實世界多階段衰退模型
# ==========================================
st.title("🛡️ 美股智慧量化估值系統 (含長線衰退模型)")

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
                    st.write("### 🧠 智慧量化模型分析 (第1年基礎)")
                    
                    # 第一年的初始爆發成長率
                    initial_growth_rate = ((forward_eps - trailing_eps) / trailing_eps) * 100
                    initial_target_pe = min(initial_growth_rate * 1.5, 55.0) 
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("初始 EPS 成長率", f"{initial_growth_rate:.2f}%")
                    c2.metric("初始推算 P/E", f"{initial_target_pe:.2f}x")
                    c3.metric("目前 PEG 值", f"{forward_pe / initial_growth_rate:.2f}")

                    # --- 10年真實世界預測表 (導入衰退與通膨) ---
                    st.write("#### ⏳ 真實世界長線股價預測 (考慮成長衰退與通膨)")
                    st.caption("模型假設：公司無法永遠維持爆發成長。第10年成長率將衰退至 6%，本益比將收斂至 25 倍，且每年扣除 3% 通貨膨脹率。")
                    
                    # 設定真實世界參數
                    terminal_growth = 6.0 # 第10年只剩6%成長
                    terminal_pe = 25.0    # 終極本益比降到25倍
                    inflation_rate = 3.0  # 每年3%通膨
                    
                    projection_data = []
                    current_eps = forward_eps
                    
                    # 逐年模擬計算
                    for year in range(1, 11):
                        # 1. 計算當年度的衰退成長率 (線性遞減)
                        # 例如: 從 40% 慢慢每年扣一點，直到第 10 年變成 6%
                        decay_factor = (year - 1) / 9.0  # 0 到 1
                        current_growth = initial_growth_rate - (initial_growth_rate - terminal_growth) * decay_factor
                        
                        # 第一年用 forward_eps，第二年起開始用當年的成長率滾動
                        if year > 1:
                            current_eps = current_eps * (1 + current_growth / 100)
                            
                        # 2. 計算當年度的估值收縮 (P/E 慢慢降低)
                        current_pe = initial_target_pe - (initial_target_pe - terminal_pe) * decay_factor
                        
                        # 3. 計算名目股價 (表面上看到的股價)
                        nominal_price = current_eps * current_pe
                        
                        # 4. 計算實質股價 (扣除通膨後的真實購買力)
                        real_price = nominal_price / ((1 + inflation_rate / 100) ** year)
                        
                        total_real_return = ((real_price - current_price) / current_price) * 100
                        
                        # 只取特定年份顯示在表格中
                        if year in [1, 2, 5, 10]:
                            projection_data.append({
                                "時間": f"{year} 年後",
                                "當下成長率": f"{current_growth:.1f}%",
                                "給予本益比": f"{current_pe:.1f}x",
                                "預估 EPS": f"${current_eps:.2f}",
                                "帳面股價 (名目)": f"${nominal_price:.2f}",
                                "真實價值 (扣通膨)": f"${real_price:.2f}",
                                "實質報酬率": f"{total_real_return:.2f}%"
                            })
                    
                    st.table(pd.DataFrame(projection_data))

                else:
                    st.warning("⚠️ 此標的獲利成長動能不足或為 ETF，不適用智慧成長模型。")
            
        except Exception as e:
            st.error(f"分析失敗: {e}")
