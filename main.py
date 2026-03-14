import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from gnews import GNews
from datetime import datetime
import pandas as pd
import io

# 1. 환경 설정 및 API 키 로드
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# 2. Gemini AI 설정 (사용자님 환경에 최적화된 Gemini 3 Flash 적용)
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    try:
        # 404 에러 방지를 위해 사용자님 화면에서 확인된 최신 모델명을 우선 사용합니다.
        model = genai.GenerativeModel('gemini-3-flash-preview')
    except:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

# 3. 페이지 기본 설정 및 세련된 디자인 적용
st.set_page_config(page_title="경제적 자유 마켓 인사이트", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    .main-title { font-size: 2.3rem; color: #1e3a8a; font-weight: 700; margin-bottom: 10px; }
    .news-card { 
        background: white; padding: 15px; border-radius: 12px; 
        border-left: 6px solid #1e3a8a; margin-bottom: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
    }
    .history-card { 
        background: #fff7ed; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #f97316; line-height: 1.6; color: #431407;
    }
    .ai-box { background-color: #f0f7ff; border-radius: 12px; padding: 25px; border: 1px solid #dbeafe; }
    </style>
    """, unsafe_allow_html=True)

# 데이터 저장 경로 설정
HISTORY_FILE = "finance_analysis_log.csv"

def load_data():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    else:
        return pd.DataFrame(columns=["날짜", "테마", "거시메모", "미시메모", "AI역사분석", "AI종합통찰"])

# 4. 사이드바: 증시 & 부동산 필승 테마 설정
st.sidebar.title("🧭 마켓 분석 나침반")

themes = {
    "💵 통화 가치와 환율": "환율 전망 OR 달러 인덱스 OR 엔저 현상 OR 환율 변동성",
    "🏦 금리와 유동성": "기준금리 OR 한국은행 OR 연준 FOMC OR 통화량 M2",
    "📉 고용과 물가": "실업률 지표 OR 소비자물가 CPI OR 인플레이션 OR 고용 보고서",
    "🐳 외국인·기관 수급": "외국인 순매수 OR 수급 특징주 OR 기관 매수 종목",
    "🏠 부동산 정책/시장": "부동산 정책 OR 아파트 매매 지수 OR 주택담보대출 금리 OR 재건축 전망",
    "📈 내 관심 종목 추적": "stock_mode"
}

selected_theme = st.sidebar.selectbox("오늘 집중할 경제 테마를 고르세요", list(themes.keys()))

if themes[selected_theme] == "stock_mode":
    stock_input = st.sidebar.text_input("추적할 종목명 입력 (예: 삼성전자)", "삼성전자")
    search_query = f"{stock_input} 전망 OR {stock_input} 실적 OR {stock_input} 뉴스"
else:
    search_query = themes[selected_theme]
    stock_input = "-"

st.sidebar.divider()
st.sidebar.info("💡 거시 지표는 부동산과 증시를 움직이는 가장 큰 동력입니다.")

# 5. 메인 화면 헤더
st.markdown(f'<p class="main-title">📈 {selected_theme}: 오늘과 과거의 대조</p>', unsafe_allow_html=True)
st.write(f"분석 기준일: {datetime.now().strftime('%Y-%m-%d')}")

tab1, tab2, tab3 = st.tabs(["🔍 시장 뉴스 & 역사 비교", "🤖 AI 통합 마켓 브리핑", "📚 분석 데이터 관리"])

today_news_titles = ""

# --- Tab 1: 오늘의 뉴스 & 역사적 사례 비교 ---
with tab1:
    col_now, col_history = st.columns(2)
    
    with col_now:
        st.subheader("🌞 오늘의 핵심 상황")
        try:
            gn = GNews(language='ko', country='KR', period='1d', max_results=5)
            # 검색어가 복잡할 경우를 대비한 쿼리 정제
            q = " OR ".join(search_query.split()) if "OR" not in search_query else search_query
            news = gn.get_news(q)
            if news:
                for n in news:
                    st.markdown(f'<div class="news-card"><a href="{n["url"]}" target="_blank" style="text-decoration:none; color:#1e3a8a; font-weight:700;">🔗 {n["title"]}</a><br><small>{n["publisher"]["title"]}</small></div>', unsafe_allow_html=True)
                    today_news_titles += f"- {n['title']}\n"
            else:
                st.write("관련 뉴스를 찾을 수 없습니다. 키워드를 더 단순하게 입력해 보세요.")
        except:
            st.error("뉴스 로딩 중 오류가 발생했습니다.")

    with col_history:
        st.subheader("⏳ 역사적 데자뷔 (과거 사례)")
        if today_news_titles and gemini_api_key:
            with st.spinner("AI가 인류 경제사를 검색하여 유사 사례를 찾는 중..."):
                try:
                    hist_prompt = f"""
                    당신은 저명한 경제 역사학자입니다. 
                    오늘의 경제 테마({selected_theme})와 최신 뉴스({today_news_titles})를 바탕으로, 
                    인류 역사상 이와 가장 유사했던 경제적 사건을 하나 꼽아 비교 분석해 주세요.
                    
                    포함 내용:
                    1. 사건명 및 시기 (예: 1970년대 오일쇼크, 2000년 IT 버블 등)
                    2. 현재 상황과의 핵심 유사점
                    3. 당시 주식, 부동산 등 자산 가격의 움직임과 결과
                    4. 지금의 투자자가 얻어야 할 역사적 교훈
                    """
                    history_res = model.generate_content(hist_prompt)
                    st.markdown(f'<div class="history-card">{history_res.text}</div>', unsafe_allow_html=True)
                    st.session_state.history_text = history_res.text
                except Exception as e:
                    st.write(f"역사 데이터를 불러오지 못했습니다: {e}")
        else:
            st.info("뉴스를 먼저 수집하거나 API 키를 확인해 주세요.")

# --- Tab 2: AI 통합 분석 및 메모 ---
with tab2:
    st.header("📝 AI 통합 인사이트 리포트")
    
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        macro_note = st.text_area("거시(Macro) 관점 메모", placeholder="금리, 환율 등 시장 전반에 대한 생각을 적어주세요.", height=150)
    with col_n2:
        micro_note = st.text_area("미시(Micro)/종목 메모", placeholder="개별 기업이나 부동산 정책 등에 대한 생각을 적어주세요.", height=150)

    if 'final_analysis' not in st.session_state:
        st.session_state.final_analysis = ""

    if st.button("🤖 종합 마켓 브리핑 요청하기"):
        if not gemini_api_key:
            st.error("Gemini API 키를 확인해 주세요.")
        else:
            with st.spinner("오늘의 데이터와 과거의 교훈을 결합 중입니다..."):
                try:
                    final_prompt = f"""
                    전문 투자 분석가로서 아래 정보를 종합하여 오늘의 리포트를 작성해줘.
                    
                    [오늘의 뉴스] {today_news_titles}
                    [역사적 사례] {st.session_state.get('history_text', '정보 없음')}
                    [사용자 메모] 거시: {macro_note}, 미시: {micro_note}
                    
                    분석 요청:
                    1. 과거 역사와 비교했을 때, 현재 우리가 가장 경계해야 할 '리스크'는 무엇인가?
                    2. 사용자 메모를 바탕으로 볼 때, 투자 전략에서 수정이 필요한 부분이 있는가?
                    3. 장기적인 경제적 자유(10년 뒤 해외 거주 등)를 위해 오늘 실천해야 할 투자 태도.
                    """
                    response = model.generate_content(final_prompt)
                    st.session_state.final_analysis = response.text
                except Exception as e:
                    st.error(f"분석 중 오류 발생: {e}")

    if st.session_state.final_analysis:
        st.markdown(f'<div class="ai-box"><h3>🤖 AI 종합 통찰 결과</h3>{st.session_state.final_analysis}</div>', unsafe_allow_html=True)

    if st.button("💾 이 분석 결과를 데이터베이스에 저장"):
        new_entry = {
            "날짜": datetime.now().strftime('%Y-%m-%d'),
            "테마": selected_theme,
            "거시메모": macro_note,
            "미시메모": micro_note,
            "AI역사분석": st.session_state.get('history_text', ''),
            "AI종합통찰": st.session_state.final_analysis
        }
        df = load_data()
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(HISTORY_FILE, index=False, encoding='utf-8-sig')
        st.balloons()
        st.success("오늘의 인사이트가 기록되었습니다! 10년 뒤 자산의 거름이 됩니다.")

# --- Tab 3: 누적 데이터 및 엑셀 관리 ---
with tab3:
    st.header("📚 누적 분석 데이터")
    history_df = load_data()
    if not history_df.empty:
        st.dataframe(history_df.sort_values(by="날짜", ascending=False), use_container_width=True)
        
        # 엑셀 다운로드 기능
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            history_df.to_excel(writer, index=False, sheet_name='MarketAnalysis')
        
        st.download_button(
            label="📊 전체 분석 기록 엑셀 다운로드",
            data=excel_buffer.getvalue(),
            file_name=f"finance_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("아직 기록된 분석 데이터가 없습니다.")

st.divider()
st.caption("꾸준한 기록과 객관적인 분석이 당신의 경제적 자유를 앞당깁니다.")