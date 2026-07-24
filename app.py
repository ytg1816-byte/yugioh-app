import streamlit as st
import requests
import google.generativeai as genai
import re

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

# 1. 내 API 키에서 실제로 '답변을 출력해내는' 모델을 실시간 테스트로 찾아내는 함수
@st.cache_resource
def get_working_model(api_key):
    genai.configure(api_key=api_key)
    
    # 1차: 구글 API가 제공하는 목록 중 실제 호출 테스트
    try:
        available_models = genai.list_models()
        for m in available_models:
            if 'generateContent' in m.supported_generation_methods:
                try:
                    test_model = genai.GenerativeModel(m.name)
                    test_model.generate_content("ping") # 실시간 핑 테스트
                    return test_model, m.name
                except Exception:
                    continue
    except Exception:
        pass
        
    # 2차: 자주 사용되는 표준 모델명 후보군 직접 테스트
    candidate_names = [
        'models/gemini-1.5-flash',
        'models/gemini-1.5-flash-latest',
        'models/gemini-1.5-pro',
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

# 모델 연결
model, active_model_name = get_working_model(gemini_api_key)

if not model:
    st.sidebar.error("❌ 연결 가능한 Gemini 모델을 찾지 못했습니다. API 키 권한을 확인해주세요.")
    st.error("Gemini API 서버와 연결할 수 없습니다. API 키가 올바른지 확인해주세요.")
    st.stop()
else:
    st.sidebar.success(f"✅ 연결 성공! ({active_model_name})")

# AI 기반 카드 데이터 추출 함수
def get_card_data_via_ai(query):
    prompt = f"""
    당신은 유희왕 카드 데이터베이스 전문가입니다.
    사용자가 입력한 검색어: '{query}' (줄임말, 별명, 한국어 카드명 가능)

    다음 세 가지 정보를 아래 양식에 맞게 정확히 출력하세요:
    
    ENGLISH_NAME: (YGOProDeck DB에서 검색되는 정확한 공식 영문 카드명만 작성. 따옴표나 특수기호 제외)
    KOREAN_NAME: (공식 한국어 카드명)
    KOREAN_INFO: (종족/속성/레벨/공수 및 OCG 공식 한국어 카드 효과 텍스트)
    """
    
    response = model.generate_content(prompt)
    response_text = response.text
    
    eng_name = ""
    kor_name = query
    kor_info = ""
    
    for line in response_text.split('\n'):
        if line.startswith("ENGLISH_NAME:"):
            eng_name = line.replace("ENGLISH_NAME:", "").strip()
            eng_name = re.sub(r'[\'"`\*]', '', eng_name)
        elif line.startswith("KOREAN_NAME:"):
            kor_name = line.replace("KOREAN_NAME:", "").strip()
        elif line.startswith("KOREAN_INFO:"):
            kor_info = line.replace("KOREAN_INFO:", "").strip()
            
    if not kor_info:
        kor_info = response_text
        
    return eng_name, kor_name, kor_info

# YGOProDeck 이미지 조회 함수
def get_image_from_ygoprodeck(eng_name):
    if not eng_name:
        return None
    url = "https://db.ygoprodeck.com/api/v7/cardinfo.php"
    params = {"fname": eng_name}
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('data', [])
    return None

tab1, tab2 = st.tabs(["🔍 스마트 카드 검색", "🧠 AI 전술 & 전개 상담"])

# --- 탭 1: 카드 검색 ---
with tab1:
    st.subheader("카드 정보 조회 (한국어로 편하게 검색!)")
    search_query = st.text_input("카드 이름 입력 (예: 마새데, 우라라, 증쥐)", key="search_input")
    
    if st.button("검색", key="search_btn"):
        if search_query:
            with st.spinner("AI가 카드를 분석하고 DB를 조회 중이야..."):
                try:
                    eng_name, kor_name, kor_info = get_card_data_via_ai(search_query)
                    cards = get_image_from_ygoprodeck(eng_name)
                    
                    st.markdown(f"### 🃏 {kor_name} ({eng_name})")
                    
                    if cards:
                        card = cards[0]
                        if 'card_images' in card and card['card_images']:
                            st.image(card['card_images'][0]['image_url'], width=280)
                    else:
                        st.info("💡 카드 이미지를 찾지 못했지만, AI 분석 결과는 아래와 같아.")
                    
                    st.markdown("#### 📜 공식 한국어 정보")
                    st.markdown(kor_info)
                    
                except Exception as e:
                    st.error(f"검색 중 에러가 발생했어: {e}")

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
                    st.error(f"답변을 불러오지 못했어. (에러: {e})")
