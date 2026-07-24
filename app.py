import streamlit as st
import requests
import google.generativeai as genai

# 페이지 기본 설정 (모바일 앱 스타일)
st.set_page_config(page_title="유희왕 AI 어시스턴트", page_icon="🃏", layout="centered")

st.title("🃏 유희왕 AI 어시스턴트")
st.caption("YGOProDeck 데이터베이스 & Gemini AI 연동 어시스턴트")

# 사이드바: API 키 입력
st.sidebar.header("⚙️ 설정")
gemini_api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")

if not gemini_api_key:
    st.info("👈 왼쪽 사이드바에 Gemini API Key를 입력해야 어플을 사용할 수 있습니다.")
    st.stop()

# Gemini AI 설정
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# YGOProDeck 카드 검색 함수 (환각 방지용 데이터 조회)
def get_card_info(card_name):
    url = f"https://db.ygoprodeck.com/api/v7/cardinfo.php?fname={card_name}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('data', [])
    return None

# 탭 구성: 카드 검색 & 전술/전개 도우미
tab1, tab2 = st.tabs(["🔍 카드 공식 DB 검색", "🧠 AI 전술/전개 상담"])

with tab1:
    st.subheader("카드 정보 조회")
    search_query = st.text_input("카드 이름을 입력하세요 (영문/일부 명칭 가능)", key="search_input")
    if st.button("검색", key="search_btn"):
        if search_query:
            cards = get_card_info(search_query)
            if cards:
                for card in cards[:3]: # 상위 3개 검색결과
                    st.markdown(f"### {card['name']}")
                    if 'card_images' in card and card['card_images']:
                        st.image(card['card_images'][0]['image_url'], width=200)
                    st.write(f"**종류:** {card.get('type', 'N/A')} | **속성/종족:** {card.get('attribute', 'N/A')} / {card.get('race', 'N/A')}")
                    st.write(f"**효과 설명:**\n{card.get('desc', '설명 없음')}")
                    st.divider()
            else:
                st.error("카드를 찾을 수 없습니다. 명칭을 확인해 주세요.")

with tab2:
    st.subheader("덱 빌딩 및 전개법 AI 상담")
    user_prompt = st.text_area("질문 내용을 입력하세요 (예: '상급 드래곤 덱 전개 공식', '특정 카드 중심의 맞춤 덱 구성 추천')", height=120)
    if st.button("AI 분석 요청", key="ai_btn"):
        if user_prompt:
            with st.spinner("Gemini AI가 전술을 분석 중입니다..."):
                system_instruction = (
                    "당신은 유희왕 전문 코치 AI입니다. 사용자의 질문에 대해 명확하고 논리적인 전개법 및 "
                    "덱 구축 가이드를 제공하세요. 확실하지 않은 정보는 지어내지 말고 공식 카드 텍스트와 규칙을 기반으로 답하세요."
                )
                full_prompt = f"{system_instruction}\n\n사용자 질문: {user_prompt}"
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
