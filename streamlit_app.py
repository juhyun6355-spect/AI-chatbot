import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 기본 설정
st.set_page_config(
    page_title="Money Manager",
    page_icon="💰",
    layout="wide"
)

# --- 커스텀 CSS 및 폰트 설정 (아기자기한 디자인) ---
st.markdown("""
    <style>
    /* 구글 폰트 'Jua' 불러오기 */
    @import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');

    /* 전체 폰트 적용 */
    html, body, [class*="css"] {
        font-family: 'Jua', sans-serif;
    }

    /* 배경색: 따뜻한 크림색 */
    .stApp {
        background-color: #FFFDF5;
    }

    /* 버튼 디자인: 둥글고 입체적인 사탕 느낌 */
    .stButton > button {
        background-color: #FFB6C1; /* 파스텔 핑크 */
        color: white;
        border-radius: 25px;
        border: none;
        padding: 10px 24px;
        font-size: 18px;
        box-shadow: 0 4px 0 #FF69B4; /* 그림자 */
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #FF69B4;
        transform: scale(1.05); /* 살짝 커짐 */
        color: white;
    }
    .stButton > button:active {
        box-shadow: none;
        transform: translateY(4px); /* 눌리는 효과 */
    }

    /* 입력창 둥글게 */
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        border-radius: 15px;
        border: 2px solid #B3E5FC;
    }
    
    /* 탭 디자인 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #E1F5FE;
        border-radius: 15px 15px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #B3E5FC;
        font-weight: bold;
    }

    /* 말풍선 스타일 정의 */
    .chat-container {
        display: flex;
        align-items: flex-start;
        margin-bottom: 15px;
    }
    .ai-bubble {
        background-color: #E0F7FA; /* 파스텔 블루 */
        color: #006064;
        padding: 15px;
        border-radius: 0 20px 20px 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        margin-left: 10px;
        font-size: 18px;
    }
    </style>
""", unsafe_allow_html=True)

# 데이터 저장을 위한 session_state 초기화
if "expenses" not in st.session_state:
    st.session_state.expenses = []

# 앱 제목 및 소개
st.title("💰 머니 매니저 (Money Manager)")
st.markdown("### 🛒 우리들의 똑똑한 용돈 관리 친구")
st.info("안녕? 난 너의 용돈 관리를 도와줄 AI 코치야! 🤖\n오늘 무엇을 샀는지 알려주면 내가 멋진 조언을 해줄게!")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 마이 데이터 보드", "🤖 AI 머니 코치", "⚖️ 소비 밸런스 게임"])

# --- Tab 1: 마이 데이터 보드 ---
with tab1:
    st.subheader("📝 오늘 무엇을 샀나요?")
    
    # 입력 폼
    with st.form("input_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            item = st.text_input("물건 이름", placeholder="예: 떡볶이, 공책")
            price = st.number_input("가격 (원)", min_value=0, step=100, format="%d")
        with col2:
            category = st.selectbox("어떤 종류인가요?", ["간식 🍪", "학용품 ✏️", "장난감 🤖", "교통비 🚌", "기타 🎸"])
            is_need = st.radio("꼭 필요한 것이었나요?", ["필요해요 (Need) ✅", "원해요 (Want) 💖"], horizontal=True)
            
        submitted = st.form_submit_button("장바구니에 담기 🛒")
        
        if submitted:
            if item and price > 0:
                st.session_state.expenses.append({
                    "항목": item,
                    "가격": price,
                    "종류": category,
                    "유형": is_need
                })
                st.balloons() # 풍선 효과 추가
                st.success(f"와! '{item}'을(를) 기록장에 적었어요! 참 잘했어요 👍")
            else:
                st.error("앗! 물건 이름과 가격을 정확히 알려주세요. 🥺")

    st.divider()

    # 데이터 시각화 및 표
    if st.session_state.expenses:
        df = pd.DataFrame(st.session_state.expenses)
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("#### 🍩 어디에 돈을 많이 썼을까?")
            fig1 = px.pie(df, values="가격", names="종류", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_chart2:
            st.markdown("#### 📊 꼭 필요한 소비였을까?")
            fig2 = px.bar(df, x="유형", y="가격", color="유형", text_auto=True, color_discrete_map={"필요해요 (Need) ✅": "#4CAF50", "원해요 (Want) 💖": "#FF9800"})
            st.plotly_chart(fig2, use_container_width=True)
            
        st.markdown("#### 📋 내가 쓴 용돈 목록")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("아직 텅 비어있어요! 위에서 첫 번째 소비를 기록해보세요. 🎈")

# --- Tab 2: AI 머니 코치 ---
with tab2:
    st.subheader("🤖 AI 머니 코치")
    
    if not st.session_state.expenses:
        st.warning("아직 기록이 없어서 분석할 수 없어요. 🥺 '마이 데이터 보드'에 먼저 기록해주세요!")
    else:
        st.write("친구의 소비 습관을 보고 내가 칭찬이나 조언을 해줄게!")
        if st.button("AI 코치님, 분석해주세요! 🔍"):
            df = pd.DataFrame(st.session_state.expenses)
            
            # 데이터 계산
            total_spent = df['가격'].sum()
            snack_spent = df[df['종류'] == '간식']['가격'].sum()
            snack_ratio = (snack_spent / total_spent * 100) if total_spent > 0 else 0
            
            wants_amount = df[df['유형'] == '원해요 (Want) 💖']['가격'].sum()
            needs_amount = df[df['유형'] == '필요해요 (Need) ✅']['가격'].sum()

            st.markdown(f"### 📊 분석 결과 (총 소비: {total_spent:,}원)")

            # Rule 1: 간식 비율 체크
            if snack_ratio > 40:
                st.warning(f"🍪 **간식 경보!** 간식비가 전체의 {snack_ratio:.1f}%를 차지해요. 군것질 비율이 너무 높아요! 건강과 지갑을 위해 조금만 줄여볼까요?")
            else:
                st.success(f"🍎 **아주 좋아요!** 간식비 비율이 {snack_ratio:.1f}%로 적절해요.")

            # Rule 2: Needs vs Wants 체크
            if wants_amount > needs_amount:
                st.error("💸 **지출 주의!** '원해요(Want)'에 쓴 돈이 '필요해요(Need)'보다 많아요. 꼭 필요하지 않은 물건을 너무 많이 샀어요. 신중한 선택이 필요해요!")
            else:
                st.success("⚖️ **훌륭해요!** 꼭 필요한 곳에 돈을 잘 쓰고 있군요. 합리적인 소비 습관입니다!")

# --- Tab 3: 소비 밸런스 게임 ---
with tab3:
    st.subheader("⚖️ 소비 밸런스 게임")
    st.write("현명한 선택을 하는 연습을 해봅시다!")
    
    st.markdown("""
    **상황:**  
    용돈이 10,000원 남았는데, 두 가지 선택지 중 하나만 고를 수 있어요!
    """)
    
    col_choice1, col_choice2 = st.columns(2)
    
    # 게임 선택 상태 관리
    if "game_choice" not in st.session_state:
        st.session_state.game_choice = None

    with col_choice1:
        if st.button("✨ 한정판 캐릭터 카드 구매 (10,000원)"):
            st.session_state.game_choice = "card"
    with col_choice2:
        if st.button("🎁 친구 생일선물 업그레이드 (10,000원)"):
            st.session_state.game_choice = "gift"
            
    if st.session_state.game_choice:
        st.divider()
        
        # 결과 말풍선 표시 함수
        def show_game_result(emoji, text):
            st.markdown(f"""
            <div class="chat-container">
                <div style="font-size: 40px;">{emoji}</div>
                <div class="ai-bubble">{text}</div>
            </div>
            """, unsafe_allow_html=True)

        if st.session_state.game_choice == "card":
            show_game_result("🦊", "<b>선택 결과:</b><br>와! 희귀한 카드를 얻어서 기분이 날아갈 것 같아! ✨<br>하지만 친구 선물은 평범한 걸로 줘야 해서 조금 미안한 마음이 들 수도 있어.<br>(잃어버린 기회: 친구가 감동받는 모습)")
        else:
            show_game_result("🤖", "<b>선택 결과:</b><br>친구가 선물을 받고 정말 감동할 거야! 우정이 더 반짝반짝 빛나겠지? 💖<br>하지만 갖고 싶던 카드는 포기해야 해서 조금 아쉬울 거야.<br>(잃어버린 기회: 한정판 카드)")
            
        st.markdown("#### 📝 왜 그런 선택을 했니?")
        reason = st.text_area("이유를 적어주면 미션 성공이야!", placeholder="예: 친구가 기뻐하는 게 더 좋아서...")
        
        if reason:
            st.balloons()
            st.success("🎉 **미션 완료!** 자신의 생각을 멋지게 설명했네! 참 잘했어! 💯")
