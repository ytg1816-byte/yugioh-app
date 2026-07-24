import streamlit as st
import requests
import google.generativeai as genai
import re

# 페이지 설정
st.set_page_config(page_title="유희왕 AI 어시스턴트", page_icon="🃏", layout="centered")
st.title("🃏 유희왕 AI 어시스턴트 V2.1")
st.caption("AI 닉네임 변환 + DB 직접 조회 버전")

# 사이드바 API 설정
st.sidebar.header("⚙️ 설정")
gemini_api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")

if not gemini_api_key:
    st.info("👈 왼쪽 사이드바에 API Key를 넣어야 작동해!")
    st.stop()

# 살아있는 모델 자동 감지
@st.cache_resource
def get_working_model(api_key):
    genai.configure(api_key=api_key)
    try:
        available_models = genai.list_models()
        for m in available_models:
            if 'generateContent' in m.supported_generation_methods:
                try:
                    test_model = genai.GenerativeModel(m.name)
                    test_model.generate_content("ping")
                    return test_model, m.name
                except Exception:
                    continue
    except Exception:
        pass
        
    candidate_names = [
        'models/gemini-1.5-flash',
        'models/gemini-1.5-flash-latest',
        'gemini-1.5-flash',
        'models/gemini-2.0-flash-exp'
    ]
    for c_name in candidate_names:
        try:
            test_model = genai.GenerativeModel(c_name)
            test_model.generate_content("ping")
            return test_model, c_name
        except Exception:
            continue
    return None, None

model, active_model_name = get_working_model(gemini_api_key)

if not model:
    st.sidebar.error("❌ API 키를 확인해주세요.")
    st.stop()
else:
    st.sidebar.success(f"✅ 연결 성공! ({active_model_name})")

# 1. AI는 오직 '줄임말 ➔ 공식 영문명' 변환만 수행 (틀릴 확률 극소화)
def get_english_name_via_ai(query):
    prompt = f"유희왕 카드 '{query}' (줄임말/별명 가능)의 YGOProDeck DB용 공식 영문 카드명 딱 1개만 출력해. 설명 없이 카드명만 작성해."
    response = model.generate_content(prompt)
    eng_name = response.text.strip()
    return re.sub(r'[\'"`\*]', '', eng_name)

# 2. DB에서 100% 오피셜 데이터 및 이미지 가져오기
def get_card_from_ygoprodeck(eng_name):
    url = "https://db.ygoprodeck.com/api/v7/cardinfo.php"
    params = {"fname": eng_name}
    res = requests.get(url, params=params)
    if res.status_code == 200:
        data = res.json().get('data', [])
        if data:
            return data[0]
    return None

tab1, tab2 = st.tabs(["🔍 스마트 카드 검색", "🧠 AI 전술 & 전개 상담"])

# --- 탭 1: 카드 검색 ---
with tab1:
    st.subheader("카드 정보 조회 (DB 직접 연동)")
    search_query = st.text_input("카드 이름 입력 (예: 증쥐, 우라라, 마새데)", key="search_input")
    
    if st.button("검색", key="search_btn"):
        if search_query:
            with st.spinner("AI가 이름 해석 후 DB를 조회하는 중..."):
                try:
                    eng_name = get_english_name_via_ai(search_query)
                    card = get_card_from_ygoprodeck(eng_name)
                    
                    if card:
                        st.markdown(f"### 🃏 {card['name']}")
                        
                        # 카드 이미지 출력
                        if 'card_images' in card and card['card_images']:
                            st.image(card['card_images'][0]['image_url'], width=280)
                        
                        # DB에서 직접 가져온 오피셜 상세 정보
                        st.markdown("#### 📜 DB 오피셜 스탯 & 영어 효과")
                        st.write(f"**Type:** {card.get('type', '-')}")
                        st.write(f"**Attribute / Race:** {card.get('attribute', '-') if 'attribute' in card else '-'} / {card.get('race', '-')}")
                        if 'atk' in card:
                            st.write(f"**ATK / DEF:** {card.get('atk', 0)} / {card.get('def', 0)}")
                        st.info(card.get('desc', '효과 정보 없음'))
                        
                    else:
                        st.warning(f"DB에서 '{eng_name}' 카드를 찾지 못했어. 풀네임으로 다시 검색해봐!")
                        
                except Exception as e:
                    st.error(f"검색 오류: {e}")

# --- 탭 2: 전개법 상담 ---
with tab2:
    st.subheader("덱 빌딩 및 전개법 상담")
    user_prompt = st.text_area("질문을 편하게 던져봐 (예: '마탄환 데먼스미스 전개법')", height=120)
    
    if st.button("AI 분석 요청", key="ai_btn"):
        if user_prompt:
            with st.spinner("AI 분석 중..."):
                try:
                    system_instruction = "당신은 유희왕 마스터 듀얼 1티어 플레이어입니다. 한국어로 정확하고 실전적인 전개법과 팁을 알려주세요."
                    response = model.generate_content(f"{system_instruction}\n\n질문: {user_prompt}")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"답변 실패: {e}")
