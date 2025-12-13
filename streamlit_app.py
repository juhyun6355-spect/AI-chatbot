import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 기본 설정
st.set_page_config(
    page_title="Money Manager",
    page_icon="💰",
    layout="wide"
)

# 데이터 저장을 위한 session_state 초기화
if "expenses" not in st.session_state:
    st.session_state.expenses = []

# 앱 제목 및 소개
st.title("💰 Money Manager (머니 매니저)")
st.markdown("### 초등학생을 위한 똑똑한 용돈 관리 도우미 🛒")
st.info("내 용돈을 기록하고, AI 코치의 조언을 들어보세요! 합리적인 소비 습관을 길러봐요.")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 마이 데이터 보드", "🤖 AI 머니 코치", "⚖️ 소비 밸런스 게임"])

# --- Tab 1: 마이 데이터 보드 ---
with tab1:
    st.subheader("📝 오늘의 소비 기록")
    
    # 입력 폼
    with st.form("input_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            item = st.text_input("무엇을 샀나요?", placeholder="예: 떡볶이, 공책")
            price = st.number_input("얼마인가요?", min_value=0, step=100, format="%d")
        with col2:
            category = st.selectbox("종류", ["간식", "학용품", "장난감", "교통비", "기타"])
            is_need = st.radio("소비 유형", ["필요해요 (Need) ✅", "원해요 (Want) 💖"], horizontal=True)
            
        submitted = st.form_submit_button("기록하기")
        
        if submitted:
            if item and price > 0:
                st.session_state.expenses.append({
                    "항목": item,
                    "가격": price,
                    "종류": category,
                    "유형": is_need
                })
                st.success(f"{item} 기록 완료!")
            else:
                st.warning("항목과 가격을 정확히 입력해주세요.")

    st.divider()

    # 데이터 시각화 및 표
    if st.session_state.expenses:
        df = pd.DataFrame(st.session_state.expenses)
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("#### 🍩 종류별 소비 비율")
            fig1 = px.pie(df, values="가격", names="종류", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_chart2:
            st.markdown("#### 📊 Need vs Want")
            fig2 = px.bar(df, x="유형", y="가격", color="유형", text_auto=True, color_discrete_map={"필요해요 (Need) ✅": "#4CAF50", "원해요 (Want) 💖": "#FF9800"})
            st.plotly_chart(fig2, use_container_width=True)
            
        st.markdown("#### 📋 상세 내역")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("아직 기록된 내용이 없어요. 위에서 첫 번째 소비를 기록해보세요!")

# --- Tab 2: AI 머니 코치 ---
with tab2:
    st.subheader("🤖 AI 머니 코치")
    
    if not st.session_state.expenses:
        st.warning("데이터가 없어서 분석할 수 없어요. 먼저 '마이 데이터 보드'에 소비를 기록해주세요!")
    else:
        st.write("여러분의 소비 패턴을 분석해서 칭찬과 조언을 해줄게요.")
        if st.button("내 소비 분석 요청하기"):
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
        if st.session_state.game_choice == "card":
            st.info("👉 **선택 결과:** 희귀한 카드를 얻어서 기분이 날아갈 것 같아요! 하지만 친구 선물은 평범한 걸로 줘야 해서 조금 아쉬운 마음이 들 수도 있어요. (기회비용: 친구의 더 큰 기쁨)")
        else:
            st.success("👉 **선택 결과:** 친구가 선물을 받고 정말 감동할 거예요! 우정이 더 빛나겠죠? 하지만 갖고 싶던 카드는 포기해야 해요. (기회비용: 한정판 카드 소장 기회)")
            
        st.markdown("#### 📝 나의 생각 정리하기")
        reason = st.text_area("왜 그런 선택을 했나요? 이유를 적어주세요.", placeholder="이유를 입력하면 미션이 완료됩니다!")
        
        if reason:
            st.balloons()
            st.success("🎉 **미션 완료!** 자신의 선택에 대해 멋지게 설명했네요. 참 잘했어요!")
