import streamlit as st
import requests
import google.generativeai as genai

# 페이지 설정
st.set_page_config(page_title="유희왕 AI 어시스턴트", page_icon="🃏", layout="centered")
st.title("🃏 유희왕 AI 어시스턴트 V2")
st.caption("한국어 완벽 지원 & 전술 분석 도우미")

# 사이드바 API 설정
st.sidebar.header("⚙️ 설정")
gemini_api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")

if not gemini_api_key:
    st.info("👈 왼쪽 사이드바에 API Key를 넣어야 작동해!")
    st.stop()

genai.configure(api_key=gemini_api_key)
# 가장 안정적인 최신 모델로 고정
model = genai.GenerativeModel('gemini-1.5-flash')

# 한국어 ➔ 영문명 변환 및 공식 한국어 텍스트 가져오는 함수
def get_card_data_via_ai(query):
    # 1. 영문명 추출 (YGOProDeck 검색용)
    prompt_eng = f"유희왕 카드 '{query}'의 공식 영문 카드명만 딱 출력해줘. 다른 말은 절대 하지 마."
    eng_name = model.generate_content(prompt_eng).text.strip()
    
    # 2. 공식 한국어 텍스트 추출
    prompt_kor = f"유희왕 카드 '{query}'의 종족/속성/레벨 정보와 '공식 한국어 OCG 카드 효과 텍스트'를 유희왕 룰에 맞게 정확히 적어줘."
    kor_info = model.generate_content(prompt_kor).text.strip()
    
    return eng_name, kor_info

# YGOProDeck에서 이미지 및 기본 스탯 가져오는 함수
def get_image_from_ygoprodeck(eng_name):
    url = f"https://db.ygoprodeck.com/api/v7/cardinfo.php?fname={eng_name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('data', [])
    return None

tab1, tab2 = st.tabs(["🔍 스마트 카드 검색", "🧠 AI 전술 & 전개 상담"])

# --- 탭 1: 카드 검색 ---
with tab1:
    st.subheader("카드 정보 조회 (한국어로 편하게 검색!)")
    search_query = st.text_input("카드 이름 입력 (예: 하루 우라라, 증식의 G)", key="search_input")
    
    if st.button("검색", key="search_btn"):
        if search_query:
            with st.spinner("DB 뒤지는 중... 턴 엔드 하지 말고 기다려봐!"):
                try:
                    eng_name, kor_info = get_card_data_via_ai(search_query)
                    cards = get_image_from_ygoprodeck(eng_name)
                    
                    if cards:
                        card = cards[0] # 첫 번째 결과
                        st.markdown(f"### {search_query} ({card['name']})")
                        if 'card_images' in card and card['card_images']:
                            st.image(card['card_images'][0]['image_url'], width=300)
                        
                        st.markdown("#### 📜 공식 한국어 정보")
                        st.write(kor_info)
                    else:
                        st.warning(f"이미지는 못 찾았지만 정보는 가져왔어!\n\n{kor_info}")
                except Exception as e:
                    st.error(f"검색 중 에러가 났어! (에러 내용: {e})")

# --- 탭 2: 전개법 상담 ---
with tab2:
    st.subheader("덱 빌딩 및 전개법 상담")
    user_prompt = st.text_area("질문을 편하게 던져봐 (예: '마탄환과 데먼스미스 혼합 전개법 알려줘')", height=120)
    
    if st.button("AI 분석 요청", key="ai_btn"):
        if user_prompt:
            with st.spinner("AI가 최적의 전개 루트를 계산 중이야..."):
                try:
                    system_instruction = "당신은 유희왕 마스터 듀얼 및 OCG 1티어 플레이어입니다. 유저의 질문에 대해 한국어로 매우 자연스럽고 정확한 전개법, 카드 시너지, 덱 구축 팁을 제공하세요. 실전성 있는 조언을 해줘야 합니다."
                    full_prompt = f"{system_instruction}\n\n사용자 질문: {user_prompt}"
                    
                    response = model.generate_content(full_prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"답변을 불러오지 못했어. (에러: {e})\nAPI 키가 정확한지 다시 확인해 줘!")
