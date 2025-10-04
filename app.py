import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 頁面設定 ---
st.set_page_config(page_title="Wheel Strategy Analyzer v2.0", page_icon="📊", layout="wide")

st.title("📊 美股滾輪策略評估儀表板 v2.0 (Wheel Strategy Analyzer)")

# --- 輸入股票代碼 ---
ticker = st.text_input("輸入股票代碼（例如：NVDA、AAPL、MSFT）", "NVDA")

if ticker:
    data = yf.Ticker(ticker)
    info = data.info

    st.subheader(f"🎯 股票基本資訊：{info.get('shortName','N/A')} ({ticker})")
    col1, col2, col3 = st.columns(3)
    col1.metric("現價", f"${info.get('currentPrice','N/A')}")
    col2.metric("Beta", info.get("beta","N/A"))
    col3.metric("股息率", f"{info.get('dividendYield',0)*100:.2f}%")

    eps_growth = info.get("earningsQuarterlyGrowth", 0)
    iv_rank = st.slider("模擬 IV Rank (假設值)", 0, 100, 40)
    oi_score = st.slider("模擬 OI / 流動性分數", 0, 100, 70)

    # --- 抓取歷史資料 ---
    hist = data.history(period="6mo")
    hist["50MA"] = hist["Close"].rolling(50).mean()
    hist["200MA"] = hist["Close"].rolling(200).mean()

    # --- 技術圖表 ---
    st.markdown("### 📈 價格與移動均線趨勢圖")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name="收盤價", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=hist.index, y=hist["50MA"], mode="lines", name="50MA", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=hist.index, y=hist["200MA"], mode="lines", name="200MA", line=dict(color="green")))
    fig.update_layout(height=400, xaxis_title="日期", yaxis_title="價格", legend_title="指標")
    st.plotly_chart(fig, use_container_width=True)

    # --- 評分邏輯 ---
    score = (
        (0.25 * (100 - abs(iv_rank - 40))) +  # 理想中等 IV Rank
        (0.20 * oi_score) +
        (0.15 * (100 - abs((info.get("beta",1)-1)*100))) +
        (0.15 * max(0, eps_growth * 100 + 50)) +
        (0.10 * (info.get("dividendYield",0)*100*25)) +
        (0.15 * 80)  # 技術面預設中立分
    ) / 100

    st.markdown(f"### 💡 滾輪策略適配度：**{score:.1f} / 100**")

    # --- 策略建議 ---
    strategy = ""
    if score >= 80:
        strategy = f"""
        ✅ **非常適合滾輪策略**
        - 建議策略：Sell Put（價外 5–10%）+ Covered Call（價外 10–15%）
        - 週期建議：以週選為主，可每週收租滾動
        - 標的示例：{ticker} 若現價約 ${info.get('currentPrice','N/A')}，
          可考慮賣出 {round(info.get('currentPrice',0)*0.95)} Put，
          同時賣出 {round(info.get('currentPrice',0)*1.10)} Call。
        """
        st.success(strategy)
    elif score >= 60:
        strategy = f"""
        ⚖️ **中度適合滾輪策略**
        - 建議策略：Sell Put（價外 8–12%）觀察是否被指派；
          若被指派後再進行 Covered Call。
        - 週期建議：週選或月選皆可。
        - 提醒：IV 偏高時，請設定停損點（建議跌破 50MA 時中止）。 
        """
        st.info(strategy)
    else:
        strategy = f"""
        🚫 **暫不建議滾輪策略**
        - 可能原因：波動過大（IV 過高）或流動性不足。
        - 建議行動：觀察 IV Rank 是否回落到 40–50% 區間，再重新評估。
        - 或以 Sell Call Spread / Buy Put 取代滾輪收租。
        """
        st.warning(strategy)

    # --- 指標表格 ---
    st.write("🔍 主要指標摘要：")
    df = pd.DataFrame({
        "指標": ["IV Rank", "OI/流動性", "Beta", "EPS 成長率", "股息率"],
        "目前值": [iv_rank, oi_score, info.get("beta", "N/A"),
                   f"{eps_growth*100:.2f}%", f"{info.get('dividendYield',0)*100:.2f}%"]
    })
    st.table(df)

    # --- 底部註記 ---
    st.caption("© 2025 Wheel Strategy Analyzer v2.0 ｜ Powered by Yahoo Finance API + Streamlit")

