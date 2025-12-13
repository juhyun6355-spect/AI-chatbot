import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta
import calendar

# --- 데이터베이스 함수 정의 ---
def init_db():
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    # 사용자 테이블 (닉네임, 비밀번호)
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, pin TEXT)''')
    # 소비 기록 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, 
                  date TEXT, 
                  item TEXT, 
                  price INTEGER, 
                  category TEXT, 
                  type TEXT)''')
    # 수입 기록 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS income
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, 
                  date TEXT, 
                  item TEXT, 
                  price INTEGER, 
                  category TEXT)''')
    # 위시리스트 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS wishlist
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, 
                  item_name TEXT, 
                  target_price INTEGER, 
                  image_data BLOB)''')
    
    # 게이미피케이션을 위한 컬럼 추가 (기존 DB 호환성 유지)
    try:
        c.execute("ALTER TABLE users ADD COLUMN last_active_date TEXT")
    except sqlite3.OperationalError: pass
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN streak_days INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass

    conn.commit()
    conn.close()

def login_user(username, pin):
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    c.execute('SELECT pin FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    if result:
        return (True, "로그인 성공! 어서와요!") if result[0] == pin else (False, "비밀번호가 틀렸어요. 다시 확인해볼까요?")
    else:
        # 신규 유저 자동 가입
        conn = sqlite3.connect('money_manager.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (username, pin) VALUES (?, ?)', (username, pin))
        conn.commit()
        conn.close()
        return True, "새로운 친구 환영해요! 가입이 완료되었어요!"

def update_user_activity(username):
    """활동 기록 시 스트릭(연속일수)과 경험치 업데이트"""
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    
    # 현재 유저 정보 조회
    c.execute('SELECT last_active_date, streak_days, xp FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    
    if row:
        last_date_str, streak, xp = row
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # 경험치 증가 (기록당 10XP)
        new_xp = (xp if xp else 0) + 10
        
        # 스트릭 계산
        new_streak = streak if streak else 0
        if last_date_str != today_str:
            if last_date_str:
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
                if (datetime.now() - last_date).days == 1:
                    new_streak += 1 # 연속 기록
                else:
                    new_streak = 1 # 끊김, 다시 시작
            else:
                new_streak = 1 # 첫 기록
        
        c.execute('UPDATE users SET last_active_date = ?, streak_days = ?, xp = ? WHERE username = ?', 
                  (today_str, new_streak, new_xp, username))
    
    conn.commit()
    conn.close()

def get_user_stats(username):
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    c.execute('SELECT streak_days, xp FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result if result else (0, 0)

def add_expense_db(username, date, item, price, category, type_val):
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    c.execute('INSERT INTO expenses (username, date, item, price, category, type) VALUES (?, ?, ?, ?, ?, ?)',
              (username, str(date), item, price, category, type_val))
    conn.commit()
    conn.close()
    update_user_activity(username) # 활동 업데이트

def get_expenses_db(username):
    conn = sqlite3.connect('money_manager.db')
    df = pd.read_sql_query("SELECT * FROM expenses WHERE username = ? ORDER BY date DESC", conn, params=(username,))
    conn.close()
    return df

def add_income_db(username, date, item, price, category):
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    c.execute('INSERT INTO income (username, date, item, price, category) VALUES (?, ?, ?, ?, ?)',
              (username, str(date), item, price, category))
    conn.commit()
    conn.close()
    update_user_activity(username) # 활동 업데이트

def get_income_db(username):
    conn = sqlite3.connect('money_manager.db')
    df = pd.read_sql_query("SELECT * FROM income WHERE username = ? ORDER BY date DESC", conn, params=(username,))
    conn.close()
    
    # 빈 데이터 처리: 데이터가 없어도 'price' 컬럼이 포함된 DataFrame 반환
    if df.empty:
        return pd.DataFrame(columns=['id', 'username', 'date', 'item', 'price', 'category'])
    return df

def add_wishlist_db(username, item_name, target_price, image_data):
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    # 목표는 하나만 설정 가능하도록 기존 목표 삭제 (심플 버전)
    c.execute('DELETE FROM wishlist WHERE username = ?', (username,))
    c.execute('INSERT INTO wishlist (username, item_name, target_price, image_data) VALUES (?, ?, ?, ?)',
              (username, item_name, target_price, image_data))
    conn.commit()
    conn.close()

def get_wishlist_db(username):
    conn = sqlite3.connect('money_manager.db')
    c = conn.cursor()
    c.execute('SELECT * FROM wishlist WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result

# 앱 시작 시 DB 초기화
init_db()

# 페이지 기본 설정
st.set_page_config(
    page_title="Money Manager",
    page_icon="💰",
    layout="wide"
)

# --- 사이드바: 테마 설정 ---
with st.sidebar:
    st.header("🎨 디자인 설정")
    st.write("나만의 테마 색깔을 골라보세요!")
    theme_color = st.color_picker("메인 테마 색상", "#FFB6C1") # 기본값: 파스텔 핑크

# --- 커스텀 CSS 및 폰트 설정 (동적 테마 적용) ---
st.markdown(f"""
    <style>
    /* 구글 폰트 'Jua' 불러오기 */
    @import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');

    /* 전체 폰트 적용 */
    html, body, [class*="css"] {{
        font-family: 'Jua', sans-serif;
    }}

    /* 배경색: 따뜻한 크림색 */
    .stApp {{
        background-color: #FFFDF5;
    }}

    /* 버튼 디자인: 둥글고 입체적인 사탕 느낌 */
    .stButton > button {{
        background-color: {theme_color};
        color: white;
        border-radius: 25px;
        border: none;
        padding: 10px 24px;
        font-size: 18px;
        box-shadow: 0 4px 0 rgba(0,0,0,0.1);
        transition: all 0.2s;
    }}
    .stButton > button:hover {{
        filter: brightness(90%);
        transform: scale(1.05); /* 살짝 커짐 */
        color: white;
    }}
    .stButton > button:active {{
        box-shadow: none;
        transform: translateY(4px); /* 눌리는 효과 */
    }}

    /* 입력창 둥글게 */
    .stTextInput > div > div > input, .stNumberInput > div > div > input {{
        border-radius: 15px;
        border: 2px solid {theme_color};
    }}
    
    /* 탭 디자인 */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: #E1F5FE;
        border-radius: 15px 15px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {theme_color};
        color: white !important;
        font-weight: bold;
    }}

    /* 말풍선 스타일 정의 */
    .chat-container {{
        display: flex;
        align-items: flex-start;
        margin-bottom: 15px;
    }}
    .ai-bubble {{
        background-color: {theme_color};
        color: #333333;
        padding: 15px;
        border-radius: 0 20px 20px 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        margin-left: 10px;
        font-size: 18px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 로그인 화면 로직 ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.title("🔐 머니 매니저 로그인")
    st.markdown("### 내 용돈 기입장을 열어볼까요?")
    
    with st.form("login_form"):
        username = st.text_input("닉네임 (이름)", placeholder="예: 짱구")
        pin = st.text_input("비밀번호 (숫자 4자리)", type="password", max_chars=4, placeholder="예: 1234")
        submit_login = st.form_submit_button("시작하기 🚀")
        
        if submit_login:
            if username and len(pin) == 4:
                success, msg = login_user(username, pin)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("닉네임과 4자리 비밀번호를 정확히 입력해주세요!")
    st.stop() # 로그인 전에는 아래 내용 숨김

# 앱 제목 및 소개
st.title("💰 머니 매니저 (Money Manager)")
st.markdown(f"### 🛒 **{st.session_state.username}** 친구의 똑똑한 용돈 관리")

# --- 게이미피케이션 정보 (사이드바/상단) ---
streak_days, user_xp = get_user_stats(st.session_state.username)
user_level = (user_xp // 100) + 1 # 100XP 마다 레벨업

# 레벨별 캐릭터 및 칭호
if user_level < 3:
    char_icon = "👶"
    level_title = "용돈 초보"
elif user_level < 7:
    char_icon = "👦"
    level_title = "저축 어린이"
else:
    char_icon = "🦸"
    level_title = "소비 마스터"

col_info, col_logout = st.columns([4, 1])
with col_info:
    st.info(f"안녕? 난 너의 AI 코치야! 🤖 (Lv.{user_level} {level_title})\n오늘도 기록하러 왔구나! 참 잘했어!")
with col_logout:
    if st.button("로그아웃 👋"):
        st.session_state.logged_in = False
        st.rerun()

# 사이드바에 내 정보 표시
with st.sidebar:
    st.divider()
    st.subheader(f"내 정보 {char_icon}")
    st.write(f"**레벨:** Lv.{user_level} ({level_title})")
    st.progress(min((user_xp % 100) / 100, 1.0)) # 경험치 바
    st.caption(f"다음 레벨까지 {100 - (user_xp % 100)} XP 남음")
    
    st.write(f"**연속 기록:** {streak_days}일째 🔥")
    if streak_days >= 3:
        st.success("불타오르고 있어요! 🔥")

# 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 마이 데이터 보드", "🤖 AI 머니 코치", "⚖️ 소비 밸런스 게임", "🎋 내 꿈 저금통", "🏆 나의 트로피"])

# --- Tab 1: 마이 데이터 보드 ---
with tab1:
    st.subheader("📝 용돈기입장")
    
    # 입력 폼
    with st.form("input_form", clear_on_submit=True):
        record_type = st.radio("무엇을 기록할까요?", ["지출 (돈을 썼어요) 💸", "수입 (돈을 받았어요) 💰"], horizontal=True)
        
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("날짜", datetime.now())
            item = st.text_input("내용", placeholder="예: 떡볶이, 용돈")
            price = st.number_input("금액 (원)", min_value=0, step=100, format="%d")
        with col2:
            if "지출" in record_type:
                category = st.selectbox("어떤 종류인가요?", ["간식 🍪", "학용품 ✏️", "장난감 🤖", "교통비 🚌", "기타 🎸"])
                is_need = st.radio("꼭 필요한 것이었나요?", ["필요해요 (Need) ✅", "원해요 (Want) 💖"], horizontal=True)
            else:
                category = st.selectbox("어떤 돈인가요?", ["정기 용돈 💵", "세뱃돈 🙇", "심부름값 🧹", "칭찬 보상 ⭐", "기타 🎸"])
                is_need = None # 수입은 유형 없음
            
        submitted = st.form_submit_button("기록하기 💾")
        
        if submitted:
            if item and price > 0:
                if "지출" in record_type:
                    add_expense_db(st.session_state.username, date, item, price, category, is_need)
                    st.balloons()
                    st.success(f"💸 '{item}' 소비 기록 완료! 경험치 +10 XP 획득! ✨")
                else:
                    add_income_db(st.session_state.username, date, item, price, category)
                    st.snow() # 수입은 눈 내리는 효과 (돈이 쏟아진다!)
                    st.success(f"💰 와! '{item}' 수입 기록 완료! 경험치 +10 XP 획득! ✨")
            else:
                st.error("앗! 내용과 금액을 정확히 알려주세요. 🥺")

    st.divider()

    # 데이터 시각화 및 표
    df_expense = get_expenses_db(st.session_state.username)
    df_income = get_income_db(st.session_state.username)
    
    if not df_expense.empty:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("#### 🍩 어디에 돈을 많이 썼을까?")
            fig1 = px.pie(df_expense, values="price", names="종류", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_chart2:
            st.markdown("#### 📊 꼭 필요한 소비였을까?")
            fig2 = px.bar(df_expense, x="유형", y="price", color="유형", text_auto=True, color_discrete_map={"필요해요 (Need) ✅": "#4CAF50", "원해요 (Want) 💖": "#FF9800"})
            st.plotly_chart(fig2, use_container_width=True)
            
        st.markdown("#### 📋 지출 내역")
        st.dataframe(df_expense[['date', 'item', 'price', 'category', 'type']], use_container_width=True)
    else:
        st.info("아직 지출 기록이 없어요! 🎈")
        
    if not df_income.empty:
        st.markdown("#### 📋 수입 내역")
        st.dataframe(df_income[['date', 'item', 'price', 'category']], use_container_width=True)

    # --- 월간 캘린더 리포트 ---
    st.divider()
    st.subheader("📅 월간 캘린더 리포트")
    
    # 날짜 선택
    now = datetime.now()
    col_y, col_m = st.columns(2)
    with col_y:
        year = st.selectbox("연도", range(now.year - 1, now.year + 2), index=1, key="cal_year")
    with col_m:
        month = st.selectbox("월", range(1, 13), index=now.month - 1, key="cal_month")

    # 데이터 필터링
    if not df_expense.empty:
        df_expense['date'] = pd.to_datetime(df_expense['date'])
        df_month_exp = df_expense[(df_expense['date'].dt.year == year) & (df_expense['date'].dt.month == month)]
    else:
        df_month_exp = pd.DataFrame()

    # 캘린더 스타일
    st.markdown("""
    <style>
    .day-box {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 5px;
        height: 80px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        font-size: 14px;
        border: 2px solid #F0F0F0;
    }
    .day-num { font-weight: bold; color: #555; margin-bottom: 2px; }
    .expense-text { color: #FF6B6B; font-weight: bold; font-size: 12px; }
    .good-job { font-size: 24px; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

    # 요일 헤더
    cols = st.columns(7)
    days_list = ["월", "화", "수", "목", "금", "토", "일"]
    for i, day in enumerate(days_list):
        cols[i].markdown(f"<div style='text-align: center; font-weight: bold; color: #555;'>{day}</div>", unsafe_allow_html=True)

    # 달력 그리기
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("<div class='day-box' style='background-color: transparent; border: none; box-shadow: none;'></div>", unsafe_allow_html=True)
                else:
                    current_date = datetime(year, month, day).date()
                    daily_spent = 0
                    if not df_month_exp.empty:
                        daily_spent = df_month_exp[df_month_exp['date'].dt.date == current_date]['price'].sum()
                    
                    content = f"<div class='day-num'>{day}</div>"
                    if daily_spent > 0:
                        content += f"<div class='expense-text'>💸 -{daily_spent:,}</div>"
                    elif current_date <= datetime.now().date():
                        content += "<div class='good-job'>😊</div>"
                    st.markdown(f"<div class='day-box'>{content}</div>", unsafe_allow_html=True)

    # 월말 결산 및 AI 분석
    st.markdown("### 📊 이번 달 결산")
    total_exp_month = df_month_exp['price'].sum() if not df_month_exp.empty else 0
    total_inc_month = 0
    if not df_income.empty:
        df_income['date'] = pd.to_datetime(df_income['date'])
        df_month_inc = df_income[(df_income['date'].dt.year == year) & (df_income['date'].dt.month == month)]
        total_inc_month = df_month_inc['price'].sum()
    
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("총 수입", f"{total_inc_month:,}원")
    col_s2.metric("총 지출", f"{total_exp_month:,}원")
    col_s3.metric("남은 돈", f"{total_inc_month - total_exp_month:,}원")

    st.info(f"💡 **AI 코치의 {month}월 분석:**")
    # 지난달 비교 로직
    prev_date = datetime(year, month, 1) - timedelta(days=1)
    prev_exp = 0
    if not df_expense.empty:
        prev_exp = df_expense[(df_expense['date'].dt.year == prev_date.year) & (df_expense['date'].dt.month == prev_date.month)]['price'].sum()
    
    if prev_exp > 0:
        diff = total_exp_month - prev_exp
        if diff < 0:
            st.write(f"와우! 지난달보다 **{abs(diff):,}원**이나 적게 썼어요! 알뜰살뜰 멋져요! 👏")
        elif diff > 0:
            st.write(f"지난달보다 **{diff:,}원** 더 썼네요. 다음 달엔 조금 더 아껴볼까요? 화이팅! 💪")
        else:
            st.write("지난달이랑 똑같이 썼네요! 꾸준함이 대단해요!")
    else:
        st.write("지난달 기록이 없어서 비교할 수 없지만, 이번 달도 참 잘했어요!")

# --- Tab 2: AI 머니 코치 ---
with tab2:
    st.subheader("🤖 AI 머니 코치")
    df = get_expenses_db(st.session_state.username)
    
    if df.empty:
        st.warning("아직 기록이 없어서 분석할 수 없어요. 🥺 '마이 데이터 보드'에 먼저 기록해주세요!")
    else:
        st.write("친구의 소비 습관을 보고 내가 칭찬이나 조언을 해줄게!")
        if st.button("AI 코치님, 분석해주세요! 🔍"):
            
            # 데이터 계산
            total_spent = df['price'].sum()
            snack_spent = df[df['종류'] == '간식']['price'].sum()
            snack_ratio = (snack_spent / total_spent * 100) if total_spent > 0 else 0
            
            wants_amount = df[df['유형'] == '원해요 (Want) 💖']['price'].sum()
            needs_amount = df[df['유형'] == '필요해요 (Need) ✅']['price'].sum()

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

# --- Tab 4: 내 꿈 저금통 ---
with tab4:
    st.subheader("🎋 내 꿈 저금통 (Wish List)")
    
    # 현재 자산 계산
    total_income = get_income_db(st.session_state.username)['price'].sum()
    total_expense = get_expenses_db(st.session_state.username)['price'].sum()
    current_savings = total_income - total_expense
    
    st.info(f"💰 현재 내가 모은 돈: **{current_savings:,}원**")
    
    # 목표 가져오기
    wish = get_wishlist_db(st.session_state.username)
    
    if wish:
        # 목표가 있을 때
        item_name = wish[2]
        target_price = wish[3]
        image_data = wish[4]
        
        progress = (current_savings / target_price) * 100 if target_price > 0 else 0
        progress = min(progress, 100) # 100% 넘지 않게
        
        col_goal1, col_goal2 = st.columns([1, 2])
        with col_goal1:
            if image_data:
                st.image(image_data, caption=item_name, use_container_width=True)
            else:
                st.markdown(f"<div style='font-size:100px; text-align:center;'>🎁</div>", unsafe_allow_html=True)
        
        with col_goal2:
            st.markdown(f"### 🎯 목표: {item_name}")
            st.markdown(f"#### 필요 금액: {target_price:,}원")
            
            # 커스텀 프로그레스 바
            st.markdown(f"""
            <div style="background-color: #E0E0E0; border-radius: 15px; padding: 3px;">
                <div style="width: {progress}%; background-color: {theme_color}; height: 25px; border-radius: 12px; text-align: center; color: white; line-height: 25px; font-weight: bold; transition: width 0.5s;">
                    {progress:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("") # 여백
            
            # AI 응원 메시지
            if progress >= 100:
                st.success(f"🎉 **축하해!! 드디어 {item_name}을(를) 살 수 있어! 정말 대단해!** 🥳")
            elif progress >= 50:
                st.info(f"🔥 **와! 벌써 절반이나 모았어! {item_name}이(가) 기다리고 있어. 조금만 더 힘내!**")
            else:
                st.warning(f"🌱 **시작이 반이야! 차곡차곡 모으다 보면 금방 {item_name}을(를) 가질 수 있을 거야!**")
                
            if st.button("목표 수정/삭제하기 🗑️"):
                add_wishlist_db(st.session_state.username, "", 0, None) # 삭제 처리
                st.rerun()
    else:
        # 목표가 없을 때 입력 폼
        st.write("갖고 싶은 물건이 있나요? 목표를 세워보세요!")
        with st.form("wishlist_form"):
            w_item = st.text_input("갖고 싶은 물건 이름")
            w_price = st.number_input("얼마가 필요한가요?", min_value=0, step=1000)
            w_img = st.file_uploader("사진이 있다면 올려주세요 (선택)", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("목표 설정하기 ✨"):
                if w_item and w_price > 0:
                    img_bytes = w_img.getvalue() if w_img else None
                    add_wishlist_db(st.session_state.username, w_item, w_price, img_bytes)
                    st.success("목표가 설정되었어요! 화이팅!")
                    st.rerun()
                else:
                    st.error("물건 이름과 가격을 입력해주세요.")

# --- Tab 5: 나의 트로피 ---
with tab5:
    st.subheader("🏆 나의 트로피 (명예의 전당)")
    st.write("열심히 활동해서 멋진 배지를 모아보세요!")
    
    # 배지 획득 조건 체크
    badges = []
    
    # 1. 기록왕 (7일 연속)
    if streak_days >= 7:
        badges.append({"icon": "👑", "name": "기록왕", "desc": "7일 연속 기록 달성!"})
    else:
        badges.append({"icon": "🔒", "name": "기록왕 (잠김)", "desc": "7일 연속 기록하면 열려요!"})
        
    # 2. 저축왕 (목표 금액 10% 달성)
    # (Tab 4에서 계산된 progress 변수 활용, 없으면 0)
    current_progress = locals().get('progress', 0)
    if current_progress >= 10:
        badges.append({"icon": "🐷", "name": "저축왕", "desc": "목표 금액의 10%를 모았어요!"})
    else:
        badges.append({"icon": "🔒", "name": "저축왕 (잠김)", "desc": "목표의 10%를 모으면 열려요!"})

    # 3. 레벨업 마스터 (Lv.5 달성)
    if user_level >= 5:
        badges.append({"icon": "🎓", "name": "척척박사", "desc": "레벨 5 달성!"})
    else:
        badges.append({"icon": "🔒", "name": "척척박사 (잠김)", "desc": "레벨 5가 되면 열려요!"})

    # 배지 표시
    cols = st.columns(3)
    for i, badge in enumerate(badges):
        with cols[i]:
            st.markdown(f"""
            <div style="background-color: white; padding: 20px; border-radius: 15px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                <div style="font-size: 50px;">{badge['icon']}</div>
                <h4 style="margin: 10px 0;">{badge['name']}</h4>
                <p style="color: gray; font-size: 14px;">{badge['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
