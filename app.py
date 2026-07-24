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

# Gemini API 설정
genai.configure(api_key=gemini_api_key)

# 정식 모델 설정 (gemini-1.5-flash 사용)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    model = genai.GenerativeModel('gemini-2.0-flash')

# 통합 AI 데이터 추출 함수 (속도 개선 & 파싱 에러 방지)
def get_card_data_via_ai(query):
    prompt = f"""
    당신은 유희왕 카드 데이터베이스 전문가입니다.
    사용자가 입력한 검색어: '{query}' (줄임말, 별명, 한국어 카드명 가능)

    다음 세 가지 정보를 아래 양식에 맞게 정확히 출력하세요:
    
    ENGLISH_NAME: (YGOProDeck DB에서 검색되는 정확한 공식 영문 카드명만 작성. 따옴표나 특수기호 제외)
    KOREAN_NAME: (공식 한국어 카드명)
    KOREAN_INFO: (종족/속성/레벨/공수 및 OCG 공식 한국어 카드 효과 텍스트)
    """
    
    response = model.generate_content(prompt).text
    
    eng_name = ""
    kor_name = query
    kor_info = ""
    
    for line in response.split('\n'):
        if line.startswith("ENGLISH_NAME:"):
            eng_name = line.replace("ENGLISH_NAME:", "").strip()
            # 특수문자 및 따옴표 제거
            eng_name = re.sub(r'[\'"`\*]', '', eng_name)
        elif line.startswith("KOREAN_NAME:"):
            kor_name = line.replace("KOREAN_NAME:", "").strip()
        elif line.startswith("KOREAN_INFO:"):
            kor_info = line.replace("KOREAN_INFO:", "").strip()
            
    if not kor_info:
        kor_info = response
        
    return eng_name, kor_name, kor_info

# YGOProDeck 이미지 안전 조회 함수
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
                        st.info(f"💡 카드 이미지를 찾지 못했지만, AI 분석 결과는 아래와 같아.")
                    
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
                    st.error(f"답변을 불러오지 못했어. (에러: {e})\nAPI 키가 정확한지 다시 확인해 줘!")
