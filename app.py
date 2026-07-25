import streamlit as st
import sqlite3

# 페이지 기본 설정
st.set_page_config(page_title="유희왕 로컬 카탈로그", page_icon="🃏", layout="wide")

DB_FILE = "yugioh_kr.db"

# DB 연결 및 카드 검색 함수
def search_cards(keyword):
    if not keyword.strip():
        return []
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 한국어 카드명 검색 (0.01초 로컬 검색)
    query = "SELECT name_kr, card_type, attribute, race, level, atk, def, effect_kr, image_url FROM cards WHERE name_kr LIKE ? LIMIT 20"
    cursor.execute(query, (f"%{keyword}%",))
    rows = cursor.fetchall()
    conn.close()
    
    return rows

# 앱 헤더 UI
st.title("🃏 유희왕 초고속 카드 검색기 (V3 로컬)")
st.caption("AI 오역 없는 순수 한국어 OCG 공식 데이터베이스 연동")

# 검색창
search_term = st.text_input("카드 이름을 입력하세요 (예: 하루 우라라, 데먼스미스)", "")

if search_term:
    results = search_cards(search_term)
    
    if results:
        st.success(f"총 {len(results)}건의 카드를 찾았습니다!")
        
        for card in results:
            name, c_type, attr, race, lvl, atk, df, effect, img = card
            
            with st.expander(f"📌 {name} [{c_type}]", expanded=True):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if img:
                        st.image(img, width=200)
                    else:
                        st.write("이미지 없음")
                        
                with col2:
                    st.subheader(name)
                    st.write(f"**종류:** {c_type} | **속성:** {attr} | **종족:** {race}")
                    if "몬스터" in c_type:
                        st.write(f"**레벨/랭크/링크:** {lvl} | **공격력:** {atk} | **수비력:** {df}")
                    
                    st.markdown("---")
                    st.write("**[카드 효과]**")
                    st.info(effect)
    else:
        st.warning("일치하는 카드가 없습니다.")